# Realtime Instructions for Flutter Frontend

## Overview

The backend provides a **WebSocket endpoint** at `/ws/transactions` that broadcasts
real-time events whenever a transaction is created, updated, or deleted through the
API. No third-party services (Supabase, Firebase, etc.) are involved — it is a pure
API WebSocket.

---

## WebSocket URL

```
ws://<API_HOST>:<PORT>/ws/transactions
```

Examples:
- Local: `ws://127.0.0.1:8000/ws/transactions`
- Production: `wss://api.yourdomain.com/ws/transactions`

> Use `wss://` in production (TLS).

---

## Message Format

Every message is a JSON string with this structure:

```json
{
  "event": "INSERT" | "UPDATE" | "DELETE",
  "table": "transactions",
  "data": {
    "id": 1,
    "userID": 3,
    "timestamp": "2026-02-19T10:30:00",
    "photo": "https://example.com/photo.jpg",
    "device_id": "device001",
    "stamp_type": 0
  }
}
```

### Event Types

| Event    | When it fires                        | `data` contains          |
|----------|--------------------------------------|--------------------------|
| INSERT   | New transaction created (POST)       | Full transaction object  |
| UPDATE   | Transaction modified (PUT)           | Full updated transaction |
| DELETE   | Transaction removed (DELETE)         | `{"id": <deleted_id>}`   |

---

## Flutter Implementation

### 1. Add dependency

In `pubspec.yaml`:

```yaml
dependencies:
  web_socket_channel: ^2.4.0
```

### 2. Create a Realtime Service

```dart
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class TransactionRealtimeService {
  WebSocketChannel? _channel;
  final String wsUrl;
  final void Function(String event, Map<String, dynamic> data) onEvent;

  TransactionRealtimeService({
    required this.wsUrl,
    required this.onEvent,
  });

  void connect() {
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

    _channel!.stream.listen(
      (message) {
        final decoded = jsonDecode(message) as Map<String, dynamic>;
        final event = decoded['event'] as String;
        final data = decoded['data'] as Map<String, dynamic>;
        onEvent(event, data);
      },
      onError: (error) {
        print('WebSocket error: $error');
        _reconnect();
      },
      onDone: () {
        print('WebSocket closed');
        _reconnect();
      },
    );
  }

  void _reconnect() {
    Future.delayed(const Duration(seconds: 3), () {
      print('Reconnecting WebSocket...');
      connect();
    });
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }
}
```

### 3. Use in a Provider / BLoC / Controller

```dart
class TransactionProvider extends ChangeNotifier {
  List<Transaction> _transactions = [];
  late TransactionRealtimeService _realtime;

  TransactionProvider() {
    _realtime = TransactionRealtimeService(
      wsUrl: 'ws://YOUR_API_HOST:8000/ws/transactions',
      onEvent: _handleRealtimeEvent,
    );
    _realtime.connect();
    _loadTransactions(); // Initial fetch via REST API
  }

  void _handleRealtimeEvent(String event, Map<String, dynamic> data) {
    switch (event) {
      case 'INSERT':
        _transactions.add(Transaction.fromJson(data));
        break;
      case 'UPDATE':
        final index = _transactions.indexWhere((t) => t.id == data['id']);
        if (index != -1) {
          _transactions[index] = Transaction.fromJson(data);
        }
        break;
      case 'DELETE':
        _transactions.removeWhere((t) => t.id == data['id']);
        break;
    }
    notifyListeners();
  }

  Future<void> _loadTransactions() async {
    // Fetch from REST API: GET /transactions/
    // _transactions = ...
    notifyListeners();
  }

  @override
  void dispose() {
    _realtime.disconnect();
    super.dispose();
  }
}
```

### 4. Transaction Model (example)

```dart
class Transaction {
  final int id;
  final int userID;
  final DateTime timestamp;
  final String? photo;
  final String? deviceId;
  final int stampType;

  Transaction({
    required this.id,
    required this.userID,
    required this.timestamp,
    this.photo,
    this.deviceId,
    required this.stampType,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'],
      userID: json['userID'],
      timestamp: DateTime.parse(json['timestamp']),
      photo: json['photo'],
      deviceId: json['device_id'],
      stampType: json['stamp_type'],
    );
  }
}
```

---

## Architecture

```
┌──────────────┐      REST (HTTP)       ┌──────────────┐
│   Flutter     │ ──────────────────►   │   FastAPI     │
│   Frontend    │                       │   Backend     │
│               │  ◄─────────────────   │               │
│               │   WebSocket (live)    │  /ws/trans.   │
└──────────────┘                       └──────┬────────┘
                                              │
                                         ┌────▼────┐
                                         │   Any   │
                                         │   DB    │
                                         └─────────┘
```

- Flutter calls REST endpoints for CRUD operations
- Flutter listens on WebSocket for live updates
- Backend writes to DB, then broadcasts via WebSocket
- **No dependency on any specific database or service**

---

## Testing the WebSocket

### Using wscat (CLI)

```bash
npm install -g wscat
wscat -c ws://127.0.0.1:8000/ws/transactions
```

Then trigger a transaction via the API (POST/PUT/DELETE) and watch messages appear.

### Using Python

```python
import asyncio
import websockets

async def listen():
    async with websockets.connect("ws://127.0.0.1:8000/ws/transactions") as ws:
        while True:
            msg = await ws.recv()
            print(f"Received: {msg}")

asyncio.run(listen())
```

---

## Notes

- WebSocket auto-reconnect is handled client-side (see `_reconnect()` above)
- No authentication on WebSocket currently — add token auth if needed later
- Works with any database (PostgreSQL, MySQL, SQLite, etc.)
- The API server must support WebSockets (uvicorn does by default)
- No new pip dependencies required — FastAPI + uvicorn handle WebSockets natively
