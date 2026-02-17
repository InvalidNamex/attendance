# Attendance API - Frontend Integration Guide

## Flutter + Dio Implementation

This guide provides complete instructions for integrating the Attendance API into your Flutter application using the Dio HTTP client.

---

## Table of Contents
1. [API Overview](#api-overview)
2. [Setup & Configuration](#setup--configuration)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
5. [Flutter/Dio Examples](#flutterdio-examples)
6. [Error Handling](#error-handling)
7. [Photo Upload](#photo-upload)
8. [Location Features](#location-features)

---

## API Overview

**Base URL:** `https://attendance-yagn.onrender.com`

**Authentication:** HTTP Basic Authentication (username + password) for most endpoints

**Content Type:** `application/json` (except for photo uploads which use `multipart/form-data`)

**Key Features:**
- User management (registration, login, profile updates)
- Location-based settings (latitude, longitude, radius)
- Transaction tracking (check-in/check-out with photo uploads)
- Role-based access control (Admin/User)

---

## Setup & Configuration

### 1. Add Dependencies

Add Dio to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  dio: ^5.4.0
  shared_preferences: ^2.2.2  # For storing auth credentials
  geolocator: ^10.1.0  # For location features
  image_picker: ^1.0.7  # For photo capture
```

### 2. Create API Service

Create a file `lib/services/api_service.dart`:

```dart
import 'package:dio/dio.dart';

class ApiService {
  static const String baseUrl = 'https://attendance-yagn.onrender.com';
  late Dio dio;
  
  ApiService() {
    dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 60),  // Increased for Render cold starts
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    // Add interceptors for logging (optional)
    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
  }
  
  // Set Basic Auth credentials
  void setAuth(String username, String password) {
    String basicAuth = 'Basic ${base64Encode(utf8.encode('$username:$password'))}';
    dio.options.headers['Authorization'] = basicAuth;
  }
  
  // Clear auth credentials
  void clearAuth() {
    dio.options.headers.remove('Authorization');
  }
}
```

---

## Authentication

### HTTP Basic Authentication

All endpoints (except `/` root) require HTTP Basic Authentication. Include the username and password with every request.

#### Dio Implementation:

```dart
import 'dart:convert';
import 'dart:typed_data';

// Option 1: Using Basic Auth header
void setBasicAuth(Dio dio, String username, String password) {
  String basicAuth = 'Basic ${base64Encode(utf8.encode('$username:$password'))}';
  dio.options.headers['Authorization'] = basicAuth;
}

// Option 2: Using Dio's built-in BasicAuth
dio.options.headers['Authorization'] = 
  'Basic ${base64Encode(utf8.encode('$username:$password'))}';
```

### Default Credentials

On first startup, the system creates a default admin account:
- **Username:** `admin`
- **Password:** `admin123`

⚠️ **Important:** Change this password after first login!

---

## API Endpoints

### User Endpoints

#### 1. Login - POST `/users/login`

**Purpose:** Authenticate user and get user information

**Authentication:** None (credentials sent in body)

**Request Body:**
```json
{
  "userName": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "userID": 1,
  "userName": "string",
  "isAdmin": false
}
```

**Flutter/Dio Example:**
```dart
Future<Map<String, dynamic>> login(String username, String password) async {
  try {
    final response = await dio.post(
      '/users/login',
      data: {
        'userName': username,
        'password': password,
      },
    );
    
    // After successful login, set auth for future requests
    setAuth(username, password);
    
    return response.data;
  } on DioException catch (e) {
    if (e.response?.statusCode == 401) {
      throw Exception('Invalid username or password');
    }
    rethrow;
  }
}
```

---

#### 2. Create User - POST `/users/`

**Purpose:** Create a new user (Admin only)

**Authentication:** Required (HTTP Basic Auth)

**Request Body:**
```json
{
  "userName": "string",
  "password": "string",
  "deviceID": "string",  // optional
  "isAdmin": false       // optional, default: false
}
```

**Response (201):**
```json
{
  "userID": 2,
  "userName": "string",
  "deviceID": "string",
  "isAdmin": false
}
```

**Flutter/Dio Example:**
```dart
Future<Map<String, dynamic>> createUser({
  required String username,
  required String password,
  String? deviceID,
  bool isAdmin = false,
}) async {
  try {
    final response = await dio.post(
      '/users/',
      data: {
        'userName': username,
        'password': password,
        'deviceID': deviceID,
        'isAdmin': isAdmin,
      },
    );
    return response.data;
  } on DioException catch (e) {
    if (e.response?.statusCode == 400) {
      throw Exception('Username already exists');
    } else if (e.response?.statusCode == 403) {
      throw Exception('Admin access required');
    }
    rethrow;
  }
}
```

---

#### 3. Get All Users - GET `/users/`

**Purpose:** Retrieve all users

**Authentication:** Required (HTTP Basic Auth)

**Response (200):**
```json
[
  {
    "userID": 1,
    "userName": "string",
    "deviceID": "string",
    "isAdmin": true
  },
  ...
]
```

**Flutter/Dio Example:**
```dart
Future<List<Map<String, dynamic>>> getAllUsers() async {
  try {
    final response = await dio.get('/users/');
    return List<Map<String, dynamic>>.from(response.data);
  } catch (e) {
    rethrow;
  }
}
```

---

#### 4. Update User - PUT `/users/{userID}`

**Purpose:** Update user information

**Authentication:** Required (Users can update themselves, admins can update anyone)

**Request Body:** (all fields optional)
```json
{
  "userName": "string",
  "password": "string",
  "deviceID": "string"
}
```

**Response (200):**
```json
{
  "userID": 1,
  "userName": "string",
  "deviceID": "string",
  "isAdmin": false
}
```

**Flutter/Dio Example:**
```dart
Future<Map<String, dynamic>> updateUser(
  int userID, {
  String? username,
  String? password,
  String? deviceID,
}) async {
  try {
    Map<String, dynamic> data = {};
    if (username != null) data['userName'] = username;
    if (password != null) data['password'] = password;
    if (deviceID != null) data['deviceID'] = deviceID;
    
    final response = await dio.put(
      '/users/$userID',
      data: data,
    );
    return response.data;
  } on DioException catch (e) {
    if (e.response?.statusCode == 403) {
      throw Exception('Not authorized to update this user');
    } else if (e.response?.statusCode == 404) {
      throw Exception('User not found');
    }
    rethrow;
  }
}
```

---

#### 5. Delete User - DELETE `/users/{userID}`

**Purpose:** Delete a user (Admin only, cannot delete admin users)

**Authentication:** Required (Admin only)

**Response:** 204 No Content

**Flutter/Dio Example:**
```dart
Future<void> deleteUser(int userID) async {
  try {
    await dio.delete('/users/$userID');
  } on DioException catch (e) {
    if (e.response?.statusCode == 403) {
      throw Exception('Cannot delete admin users or insufficient permissions');
    } else if (e.response?.statusCode == 404) {
      throw Exception('User not found');
    }
    rethrow;
  }
}
```

---

### Settings Endpoints

#### 1. Get Settings - GET `/settings/`

**Purpose:** Get global location and time settings

**Authentication:** Required (HTTP Basic Auth)

**Response (200):**
```json
{
  "id": 1,
  "latitude": 0.0,
  "longitude": 0.0,
  "radius": 100,
  "in_time": "09:00",
  "out_time": "17:00"
}
```

**Flutter/Dio Example:**
```dart
Future<Map<String, dynamic>> getSettings() async {
  try {
    final response = await dio.get('/settings/');
    return response.data;
  } catch (e) {
    rethrow;
  }
}
```

---

#### 2. Update Settings - PUT `/settings/`

**Purpose:** Update global settings (Admin only)

**Authentication:** Required (Admin only)

**Request Body:** (all fields optional)
```json
{
  "latitude": 0.0,
  "longitude": 0.0,
  "radius": 100,
  "in_time": "09:00",
  "out_time": "17:00"
}
```

**Response (200):**
```json
{
  "id": 1,
  "latitude": 0.0,
  "longitude": 0.0,
  "radius": 100,
  "in_time": "09:00",
  "out_time": "17:00"
}
```

**Flutter/Dio Example:**
```dart
Future<Map<String, dynamic>> updateSettings({
  double? latitude,
  double? longitude,
  int? radius,
  String? inTime,
  String? outTime,
}) async {
  try {
    Map<String, dynamic> data = {};
    if (latitude != null) data['latitude'] = latitude;
    if (longitude != null) data['longitude'] = longitude;
    if (radius != null) data['radius'] = radius;
    if (inTime != null) data['in_time'] = inTime;
    if (outTime != null) data['out_time'] = outTime;
    
    final response = await dio.put(
      '/settings/',
      data: data,
    );
    return response.data;
  } catch (e) {
    rethrow;
  }
}
```

---

### Transaction Endpoints

#### 1. Create Transaction - POST `/transactions/`

**Purpose:** Create a check-in or check-out transaction with optional photo

**Authentication:** Not required

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `user_id` (required): ID of the user for this transaction
- `stamp_type` (required): 0 for check-in, 1 for check-out
- `photo` (optional): Image file

**Response (201):**
```json
{
  "id": 1,
  "userID": 1,
  "timestamp": "2026-02-17T10:30:00",
  "photo": "uploads/abc123.jpg",
  "stamp_type": 0
}
```

**Flutter/Dio Example:**
```dart
import 'package:image_picker/image_picker.dart';

Future<Map<String, dynamic>> createTransaction({
  required int userId,
  required int stampType,  // 0 = check-in, 1 = check-out
  XFile? photo,
}) async {
  try {
    FormData formData = FormData.fromMap({
      'user_id': userId,
      'stamp_type': stampType,
    });
    
    // Add photo if provided
    if (photo != null) {
      formData.files.add(MapEntry(
        'photo',
        await MultipartFile.fromFile(
          photo.path,
          filename: photo.name,
        ),
      ));
    }
    
    final response = await dio.post(
      '/transactions/',
      data: formData,
      options: Options(
        contentType: 'multipart/form-data',
      ),
    );
    return response.data;
  } on DioException catch (e) {
    if (e.response?.statusCode == 400) {
      throw Exception('Invalid stamp_type. Must be 0 or 1');
    }
    rethrow;
  }
}
```

---

#### 2. Get Transactions - GET `/transactions/`

**Purpose:** Get all transactions with optional filters

**Authentication:** Not required

**Query Parameters:** (all optional)
- `user_id`: Filter by user ID
- `stamp_type`: Filter by type (0=in, 1=out)
- `from_date`: Start date (ISO 8601 format: `2026-02-01T00:00:00`)
- `to_date`: End date (ISO 8601 format: `2026-02-15T23:59:59`)

**Response (200):**
```json
[
  {
    "id": 1,
    "userID": 1,
    "timestamp": "2026-02-17T10:30:00",
    "photo": "uploads/abc123.jpg",
    "stamp_type": 0
  },
  ...
]
```

**Flutter/Dio Example:**
```dart
Future<List<Map<String, dynamic>>> getTransactions({
  int? userId,
  int? stampType,
  DateTime? fromDate,
  DateTime? toDate,
}) async {
  try {
    Map<String, dynamic> queryParams = {};
    
    if (userId != null) queryParams['user_id'] = userId;
    if (stampType != null) queryParams['stamp_type'] = stampType;
    if (fromDate != null) queryParams['from_date'] = fromDate.toIso8601String();
    if (toDate != null) queryParams['to_date'] = toDate.toIso8601String();
    
    final response = await dio.get(
      '/transactions/',
      queryParameters: queryParams,
    );
    return List<Map<String, dynamic>>.from(response.data);
  } catch (e) {
    rethrow;
  }
}
```

---

## Flutter/Dio Examples

### Complete API Service Class

```dart
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';

class AttendanceApiService {
  static const String baseUrl = 'https://attendance-yagn.onrender.com';
  late Dio dio;
  
  AttendanceApiService() {
    dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 60),  // Increased for Render cold starts
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
  }
  
  void setAuth(String username, String password) {
    String basicAuth = 'Basic ${base64Encode(utf8.encode('$username:$password'))}';
    dio.options.headers['Authorization'] = basicAuth;
  }
  
  void clearAuth() {
    dio.options.headers.remove('Authorization');
  }
  
  // User endpoints
  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await dio.post('/users/login', data: {
      'userName': username,
      'password': password,
    });
    setAuth(username, password);
    return response.data;
  }
  
  Future<Map<String, dynamic>> createUser({
    required String username,
    required String password,
    String? deviceID,
    bool isAdmin = false,
  }) async {
    final response = await dio.post('/users/', data: {
      'userName': username,
      'password': password,
      'deviceID': deviceID,
      'isAdmin': isAdmin,
    });
    return response.data;
  }
  
  Future<List<Map<String, dynamic>>> getAllUsers() async {
    final response = await dio.get('/users/');
    return List<Map<String, dynamic>>.from(response.data);
  }
  
  Future<Map<String, dynamic>> updateUser(
    int userID, {
    String? username,
    String? password,
    String? deviceID,
  }) async {
    Map<String, dynamic> data = {};
    if (username != null) data['userName'] = username;
    if (password != null) data['password'] = password;
    if (deviceID != null) data['deviceID'] = deviceID;
    
    final response = await dio.put('/users/$userID', data: data);
    return response.data;
  }
  
  Future<void> deleteUser(int userID) async {
    await dio.delete('/users/$userID');
  }
  
  // Settings endpoints
  Future<Map<String, dynamic>> getSettings() async {
    final response = await dio.get('/settings/');
    return response.data;
  }
  
  Future<Map<String, dynamic>> updateSettings({
    double? latitude,
    double? longitude,
    int? radius,
    String? inTime,
    String? outTime,
  }) async {
    Map<String, dynamic> data = {};
    if (latitude != null) data['latitude'] = latitude;
    if (longitude != null) data['longitude'] = longitude;
    if (radius != null) data['radius'] = radius;
    if (inTime != null) data['in_time'] = inTime;
    if (outTime != null) data['out_time'] = outTime;
    
    final response = await dio.put('/settings/', data: data);
    return response.data;
  }
  
  // Transaction endpoints
  Future<Map<String, dynamic>> createTransaction({
    required int userId,
    required int stampType,
    XFile? photo,
  }) async {
    FormData formData = FormData.fromMap({
      'user_id': userId,
      'stamp_type': stampType,
    });
    
    if (photo != null) {
      formData.files.add(MapEntry(
        'photo',
        await MultipartFile.fromFile(
          photo.path,
          filename: photo.name,
        ),
      ));
    }
    
    final response = await dio.post(
      '/transactions/',
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
    );
    return response.data;
  }
  
  Future<List<Map<String, dynamic>>> getTransactions({
    int? userId,
    int? stampType,
    DateTime? fromDate,
    DateTime? toDate,
  }) async {
    Map<String, dynamic> queryParams = {};
    
    if (userId != null) queryParams['user_id'] = userId;
    if (stampType != null) queryParams['stamp_type'] = stampType;
    if (fromDate != null) queryParams['from_date'] = fromDate.toIso8601String();
    if (toDate != null) queryParams['to_date'] = toDate.toIso8601String();
    
    final response = await dio.get('/transactions/', queryParameters: queryParams);
    return List<Map<String, dynamic>>.from(response.data);
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Delete successful |
| 400 | Bad Request | Invalid data format, duplicate username |
| 401 | Unauthorized | Invalid credentials |
| 403 | Forbidden | Insufficient permissions (not admin) |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Error Handling Pattern

```dart
Future<Map<String, dynamic>> apiCall() async {
  try {
    final response = await dio.get('/endpoint');
    return response.data;
  } on DioException catch (e) {
    if (e.response != null) {
      switch (e.response!.statusCode) {
        case 400:
          throw Exception('Bad request: ${e.response!.data['detail']}');
        case 401:
          throw Exception('Unauthorized. Please login again.');
        case 403:
          throw Exception('Forbidden. Insufficient permissions.');
        case 404:
          throw Exception('Resource not found.');
        default:
          throw Exception('Server error: ${e.response!.statusCode}');
      }
    } else {
      // Network error
      throw Exception('Network error. Please check your connection.');
    }
  }
}
```

---

## Photo Upload

### Capture and Upload Photo

```dart
import 'package:image_picker/image_picker.dart';

class TransactionService {
  final AttendanceApiService apiService;
  final ImagePicker _picker = ImagePicker();
  
  TransactionService(this.apiService);
  
  Future<Map<String, dynamic>> checkInWithPhoto() async {
    // Capture photo
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1920,
      maxHeight: 1080,
      imageQuality: 85,
    );
    
    if (photo == null) {
      throw Exception('No photo captured');
    }
    
    // Create transaction with photo
    return await apiService.createTransaction(
      stampType: 0,  // 0 = check-in
      photo: photo,
    );
  }
  
  Future<Map<String, dynamic>> checkOutWithPhoto() async {
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1920,
      maxHeight: 1080,
      imageQuality: 85,
    );
    
    if (photo == null) {
      throw Exception('No photo captured');
    }
    
    return await apiService.createTransaction(
      stampType: 1,  // 1 = check-out
      photo: photo,
    );
  }
}
```

---

## Location Features

### Implementing Location Validation

```dart
import 'package:geolocator/geolocator.dart';
import 'dart:math' show cos, sqrt, asin;

class LocationService {
  final AttendanceApiService apiService;
  
  LocationService(this.apiService);
  
  // Check if user is within allowed radius
  Future<bool> isWithinAllowedLocation() async {
    // Get settings from API
    final settings = await apiService.getSettings();
    final double targetLat = settings['latitude'];
    final double targetLon = settings['longitude'];
    final int allowedRadius = settings['radius'];  // in meters
    
    // Get current location
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    
    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permissions are permanently denied');
    }
    
    Position position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
    
    // Calculate distance
    double distance = calculateDistance(
      position.latitude,
      position.longitude,
      targetLat,
      targetLon,
    );
    
    return distance <= allowedRadius;
  }
  
  // Calculate distance between two coordinates (Haversine formula)
  double calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    const double earthRadius = 6371000; // meters
    
    double dLat = _toRadians(lat2 - lat1);
    double dLon = _toRadians(lon2 - lon1);
    
    double a = (sin(dLat / 2) * sin(dLat / 2)) +
        cos(_toRadians(lat1)) *
            cos(_toRadians(lat2)) *
            sin(dLon / 2) *
            sin(dLon / 2);
    
    double c = 2 * asin(sqrt(a));
    
    return earthRadius * c;
  }
  
  double _toRadians(double degree) {
    return degree * pi / 180;
  }
  
  // Check if current time is within allowed check-in/out times
  Future<Map<String, bool>> checkTimeValidation() async {
    final settings = await apiService.getSettings();
    final String inTime = settings['in_time'];   // e.g., "09:00"
    final String outTime = settings['out_time']; // e.g., "17:00"
    
    final now = DateTime.now();
    final currentTime = TimeOfDay.fromDateTime(now);
    
    final inTimeParts = inTime.split(':');
    final outTimeParts = outTime.split(':');
    
    final allowedInTime = TimeOfDay(
      hour: int.parse(inTimeParts[0]),
      minute: int.parse(inTimeParts[1]),
    );
    
    final allowedOutTime = TimeOfDay(
      hour: int.parse(outTimeParts[0]),
      minute: int.parse(outTimeParts[1]),
    );
    
    return {
      'canCheckIn': _isAfter(currentTime, allowedInTime),
      'canCheckOut': _isAfter(currentTime, allowedOutTime),
    };
  }
  
  bool _isAfter(TimeOfDay time1, TimeOfDay time2) {
    if (time1.hour > time2.hour) return true;
    if (time1.hour < time2.hour) return false;
    return time1.minute >= time2.minute;
  }
}
```

### Complete Check-In Flow with Validation

```dart
import 'dart:math';

Future<void> performCheckIn() async {
  final locationService = LocationService(apiService);
  final transactionService = TransactionService(apiService);
  
  try {
    // 1. Verify location
    bool withinLocation = await locationService.isWithinAllowedLocation();
    if (!withinLocation) {
      throw Exception('You are not within the allowed check-in location');
    }
    
    // 2. Verify time (optional)
    final timeValidation = await locationService.checkTimeValidation();
    if (!timeValidation['canCheckIn']!) {
      // Warning: early check-in
      print('Warning: Checking in before scheduled time');
    }
    
    // 3. Capture photo and create transaction
    final result = await transactionService.checkInWithPhoto();
    
    print('Check-in successful! Transaction ID: ${result['id']}');
  } catch (e) {
    print('Check-in failed: $e');
  }
}
```

---

## Data Models (Optional)

You can create Dart models for type safety:

```dart
class User {
  final int userID;
  final String userName;
  final String? deviceID;
  final bool isAdmin;
  
  User({
    required this.userID,
    required this.userName,
    this.deviceID,
    required this.isAdmin,
  });
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      userID: json['userID'],
      userName: json['userName'],
      deviceID: json['deviceID'],
      isAdmin: json['isAdmin'],
    );
  }
}

class Settings {
  final int id;
  final double latitude;
  final double longitude;
  final int radius;
  final String inTime;
  final String outTime;
  
  Settings({
    required this.id,
    required this.latitude,
    required this.longitude,
    required this.radius,
    required this.inTime,
    required this.outTime,
  });
  
  factory Settings.fromJson(Map<String, dynamic> json) {
    return Settings(
      id: json['id'],
      latitude: json['latitude'],
      longitude: json['longitude'],
      radius: json['radius'],
      inTime: json['in_time'],
      outTime: json['out_time'],
    );
  }
}

class Transaction {
  final int id;
  final int userID;
  final DateTime timestamp;
  final String? photo;
  final int stampType;
  
  Transaction({
    required this.id,
    required this.userID,
    required this.timestamp,
    this.photo,
    required this.stampType,
  });
  
  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'],
      userID: json['userID'],
      timestamp: DateTime.parse(json['timestamp']),
      photo: json['photo'],
      stampType: json['stamp_type'],
    );
  }
  
  String get typeLabel => stampType == 0 ? 'Check-In' : 'Check-Out';
}
```

---

## Storing Credentials Securely

Use `shared_preferences` or `flutter_secure_storage` to persist login credentials:

```dart
import 'package:shared_preferences/shared_preferences.dart';

class AuthManager {
  static const String _usernameKey = 'username';
  static const String _passwordKey = 'password';
  static const String _userIDKey = 'userID';
  static const String _isAdminKey = 'isAdmin';
  
  final AttendanceApiService apiService;
  
  AuthManager(this.apiService);
  
  Future<void> login(String username, String password) async {
    // Call API
    final response = await apiService.login(username, password);
    
    // Save credentials
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_usernameKey, username);
    await prefs.setString(_passwordKey, password);
    await prefs.setInt(_userIDKey, response['userID']);
    await prefs.setBool(_isAdminKey, response['isAdmin']);
  }
  
  Future<bool> restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    final username = prefs.getString(_usernameKey);
    final password = prefs.getString(_passwordKey);
    
    if (username != null && password != null) {
      apiService.setAuth(username, password);
      return true;
    }
    return false;
  }
  
  Future<void> logout() async {
    apiService.clearAuth();
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
  
  Future<int?> getCurrentUserID() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_userIDKey);
  }
  
  Future<bool> isAdmin() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_isAdminKey) ?? false;
  }
}
```

---

## Testing the API

You can test endpoints using the interactive documentation:

**Swagger UI:** `http://your-server-url:8000/docs`

Or use Flutter to test:

```dart
void main() async {
  final api = AttendanceApiService();
  
  try {
    // Test login
    final loginResult = await api.login('admin', 'admin123');
    print('Login successful: $loginResult');
    
    // Test get settings
    final settings = await api.getSettings();
    print('Settings: $settings');
    
    // Test get transactions
    final transactions = await api.getTransactions(
      fromDate: DateTime(2026, 2, 1),
      toDate: DateTime(2026, 2, 28),
    );
    print('Transactions: ${transactions.length} found');
    
  } catch (e) {
    print('Error: $e');
  }
}
```

---

## Important Notes

1. **Base URL:** Update `baseUrl` in your API service with your actual server URL
2. **HTTPS:** Use HTTPS in production for secure communication
3. **CORS Enabled:** The API supports web clients (Flutter Web, browser apps). CORS is configured to allow all origins - restrict this in production for security
4. **Render Cold Starts:** The free tier spins down after inactivity. First requests may take 50-90 seconds. Ensure your app has adequate timeouts (60+ seconds for connectTimeout) and consider showing a loading indicator with a message like "Waking up server, please wait..."
5. **Timestamps:** All timestamps are in UTC. Convert to local time in your UI
6. **Photo Storage:** Photos are stored on the server in the `uploads/` directory
7. **Permissions:** Request camera and location permissions before using those features
8. **Error Messages:** The API returns detailed error messages in the `detail` field
9. **Rate Limiting:** Implement appropriate retry logic and timeouts
10. **Device ID:** Use a unique device identifier (e.g., from `device_info_plus` package)

---

## Support

For API documentation, visit:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`

For backend issues, check the backend logs or contact the backend team.

---

## Quick Reference

### Stamp Types
- `0` = Check-In
- `1` = Check-Out

### Time Format
- Use 24-hour format: `"HH:MM"` (e.g., `"09:00"`, `"17:30"`)

### Date Format
- ISO 8601: `"YYYY-MM-DDTHH:MM:SS"` (e.g., `"2026-02-17T10:30:00"`)

### Photo Requirements
- Accepted formats: JPG, PNG
- Recommended max size: 2MB
- Recommended resolution: 1920x1080

---

**Good luck with your Flutter implementation! 🚀**


