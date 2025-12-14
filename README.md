# TSDB Vector Server Documentation

This document provides a comprehensive guide to the **Time-Series Vector Database (TSDB Vector)** API and CLI commands.

## Getting Started

### 1. Start the Server
Run the server executable to start listening for connections (default port: `6380`).
```powershell
.\tsdb_server.exe
```
*Note: The server supports auto-loading `tsdb_data.json` on startup and real-time reloading if the file changes externally.*

### 2. Start the Client
Run the client executable to connect to the server and enter the interactive shell.
```powershell
.\tsdb_client.exe
```

### 3. Remote Access (Different PC)
If you want to access the server from another computer on the same network:

**On the Server PC:**
Run the server binding to all interfaces (`0.0.0.0`) or your specific LAN IP:
```powershell
.\tsdb_server.exe 0.0.0.0:6380
```

**On the Client PC:**
Run the client specifying the Server's IP address:
```powershell
.\tsdb_client.exe 192.168.1.X:6380
```
*(Replace `192.168.1.X` with the actual IP of the server)*

---

## CLI Commands

The following commands can be executed in the `tsdb_client` shell.

### Core Commands

#### `CREATE`
Creates a new time series.
*   **Syntax**: `CREATE <series_name> <dimension>`
*   **Example**: `CREATE sensor_data 3`
    *   Creates a series named `sensor_data` expecting vectors of dimension 3 (e.g., `[x, y, z]`).

#### `INSERT`
Inserts a new data point.
*   **Syntax**: `INSERT <series_name> <values> [key=value,key2=value2...]`
*   **Example 1 (Basic)**: `INSERT sensor_data 1.0,2.0,3.0`
*   **Example 2 (With Labels)**: `INSERT sensor_data 1.0,2.0,3.0 location=lab,sensor=active`
    *   *Note: Labels are optional string key-value pairs associated with the data point.*

#### `QUERY`
Retrieves data points from the recent past.
*   **Syntax**: `QUERY <series_name> <hours_back>`
*   **Example**: `QUERY sensor_data 1.5`
    *   Returns all data points for `sensor_data` from the last 1.5 hours.

### Vector Search & Analysis

#### `SIMILAR`
Finds similar vectors using Cosine Similarity.
*   **Syntax**: `SIMILAR <series_name> <vector> <limit> [threshold]`
*   **Arguments**:
    *   `<vector>`: Comma-separated values (must match series dimension).
    *   `<limit>`: Max number of results to return.
    *   `[threshold]` (Optional): Minimum similarity score (0.0 to 1.0).
*   **Example**: `SIMILAR sensor_data 1.0,0.0,0.0 5 0.8`
    *   Finds top 5 vectors similar to `[1,0,0]` with a similarity score >= 0.8.

#### `ANOMALY` (Matrix Profile)
Detects anomalies (discords) in the time series using Matrix Profile.
*   **Syntax**: `ANOMALY <series_name> <window_size> <k>`
*   **Arguments**:
    *   `<window_size>`: Size of the sliding window to analyze.
    *   `<k>`: Number of top anomalies to return.
*   **Example**: `ANOMALY sensor_data 10 3`
    *   Finds the top 3 most unusual 10-point subsequences.

#### `MOTIF` (Matrix Profile)
Detects motifs (recurring patterns) in the time series.
*   **Syntax**: `MOTIF <series_name> <window_size> <k>`
*   **Example**: `MOTIF sensor_data 10 3`
    *   Finds the top 3 most repeated 10-point subsequences.

### Management

#### `STATS`
Get statistics about a specific series.
*   **Syntax**: `STATS <series_name>`

#### `LIST`
List all available time series names.
*   **Syntax**: `LIST`

#### `PING`
Check server connectivity.
*   **Syntax**: `PING`

### Persistence

*Note: The server now supports **Realtime Persistence**. Data is automatically saved on every INSERT/CREATE, and external changes to `tsdb_data.json` are automatically reloaded.*

#### `SAVE`
Manually save the database to disk.
*   **Syntax**: `SAVE <path>`
*   **Example**: `SAVE backup.json`

#### `LOAD`
Manually load the database from disk.
*   **Syntax**: `LOAD <path>`
*   **Example**: `LOAD backup.json`

---

## JSON API (TCP)

If writing a custom client, send JSON strings ending with `\n` to the TCP port.

**Request Format:**
```json
{
  "Insert": {
    "series": "sensor1",
    "values": [1.0, 2.0],
    "labels": { "tag": "test" }
  }
}
```

**Response Format:**
```json
{
  "Ok": "Ok"
}
```
*or*
```json
{
  "Data": [ ... ]
}
```
