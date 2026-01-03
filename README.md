# Time Series Vector Database with Matrix Profile

A high-performance time series database with vector similarity search and Matrix Profile analysis capabilities. Built in Rust for speed and reliability.

## Features

- **Vector Time Series Storage** - Store multi-dimensional time series data
- **Similarity Search** - Find similar patterns using cosine similarity
- **Matrix Profile Analysis** - Detect anomalies and motifs in time series
- **Auto-Persistence** - Automatic save/load with graceful shutdown
- **Dual API** - CLI commands and JSON API support
- **Labels Support** - Attach key-value labels to data points

## Use Cases

### Industrial IoT & Sensor Monitoring
- Store multi-dimensional sensor data (temperature, pressure, humidity, vibration)
- Real-time anomaly detection on sensor readings
- Find recurring patterns (motifs) in operational data

### Predictive Maintenance
- Monitor machine vibration, motor current, servo position
- Early fault detection through Matrix Profile anomaly scoring
- Compare current patterns with historical normal behavior

### Infrastructure Monitoring
- Server metrics (CPU, RAM, disk I/O, network)
- Database performance monitoring
- Container and Kubernetes observability

### PLC/SCADA Systems
- Store tag values from Allen Bradley, Siemens, or other PLCs
- Detect process anomalies in manufacturing lines
- Analyze production trends and quality patterns

### Financial Time Series
- Stock price pattern analysis
- Transaction anomaly detection
- Trading signal pattern matching

## Quick Start

### Start the Server

```bash
.\tsdb_server.exe 127.0.0.1:9999
```

### Connect with CLI Client

```bash
.\tsdb_client.exe 127.0.0.1:9999
```

## CLI Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `CREATE` | `CREATE <name> <dimension>` | Create a new time series |
| `INSERT` | `INSERT <name> <val1,val2,...>` | Insert data point |
| `QUERY` | `QUERY <name>` | Query all data points |
| `LIST` | `LIST` | List all series |
| `STATS` | `STATS <name>` | Get series statistics |
| `SIMILAR` | `SIMILAR <name> <values> <k>` | Find k similar vectors |
| `ANOMALY` | `ANOMALY <name> <window> <k>` | Detect top-k anomalies |
| `MOTIF` | `MOTIF <name> <window> <k>` | Find top-k motifs |
| `PING` | `PING` | Health check |
| `HELP` | `HELP` | Show help |
| `QUIT` | `QUIT` | Exit client |

### CLI Examples

```bash
# Create a 4-dimensional series
tsdb> CREATE sensor1 4

# Insert data points
tsdb> INSERT sensor1 1.0,2.0,3.0,4.0
tsdb> INSERT sensor1 2.0,3.0,4.0,5.0
tsdb> INSERT sensor1 10.0,20.0,30.0,40.0

# Query data
tsdb> QUERY sensor1

# Find similar vectors (top 3)
tsdb> SIMILAR sensor1 1.0,2.0,3.0,4.0 3

# Detect anomalies (window=2, top-1)
tsdb> ANOMALY sensor1 2 1

# Find motifs (window=2, top-1)
tsdb> MOTIF sensor1 2 1

# Get statistics
tsdb> STATS sensor1
```

## JSON API

Send JSON commands via TCP socket to the same port.

### JSON Command Format

```json
{"type":"CommandType","data":{...}}
```

### Available JSON Commands

| Type | Data Fields | Description |
|------|-------------|-------------|
| `Ping` | - | Health check |
| `Help` | - | Show available commands |
| `CreateSeries` | `name`, `dimension` | Create series |
| `Insert` | `series`, `values` | Insert data point |
| `Query` | `series` | Query data |
| `GetStats` | `series` | Get statistics |
| `FindSimilar` | `series`, `vector`, `limit`, `threshold` | Similarity search |
| `Anomaly` | `series`, `window`, `k` | Detect anomalies |
| `Motif` | `series`, `window`, `k` | Find motifs |
| `ExportSeries` | `series` | Export series data |
| `Flush` | - | Flush buffers to storage |
| `Load` | `path` | Load database from file |

### JSON API Examples

#### Ping
```json
{"type":"Ping"}
// Response: {"status":"Pong"}
```

#### Create Series
```json
{"type":"CreateSeries","data":{"name":"sensor1","dimension":4}}
// Response: {"status":"Success","data":"Series 'sensor1' created with dimension 4"}
```

#### Insert Data
```json
{"type":"Insert","data":{"series":"sensor1","values":[1.0,2.0,3.0,4.0]}}
// Response: {"status":"Success","data":"Inserted 4 values into 'sensor1'"}
```

#### Query Data
```json
{"type":"Query","data":{"series":"sensor1"}}
// Response: {"status":"Data","data":[{"timestamp":...,"values":[1.0,2.0,3.0,4.0],"labels":{}}]}
```

#### Get Statistics
```json
{"type":"GetStats","data":{"series":"sensor1"}}
// Response: {"status":"Stats","data":{"series":"sensor1","dimension":4,"points_in_memory":3,"total_points":3}}
```

#### Find Similar Vectors
```json
{"type":"FindSimilar","data":{"series":"sensor1","vector":[1.0,2.0,3.0,4.0],"limit":3,"threshold":0.5}}
// Response: {"status":"Similar","data":[{"timestamp":...,"similarity":0.99,"values":[...],"labels":{}}]}
```

#### Detect Anomalies
```json
{"type":"Anomaly","data":{"series":"sensor1","window":2,"k":1}}
// Response: {"status":"Anomalies","data":[{"start_timestamp":...,"end_timestamp":...,"score":8.06,"window_size":2}]}
```

#### Find Motifs
```json
{"type":"Motif","data":{"series":"sensor1","window":2,"k":1}}
// Response: {"status":"Motifs","data":[{"start_timestamp":...,"end_timestamp":...,"score":8.06,"window_size":2}]}
```

### Using JSON API with PowerShell

```powershell
$client = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 9999)
$stream = $client.GetStream()
$writer = New-Object System.IO.StreamWriter($stream)
$reader = New-Object System.IO.StreamReader($stream)

# Send command
$json = '{"type":"Ping"}'
$writer.WriteLine($json)
$writer.Flush()

# Read response
$response = $reader.ReadLine()
Write-Host $response

$client.Close()
```

## Data Persistence

- **Auto-Save**: Data automatically saved to `tsdb_data.json` every 60 seconds
- **Auto-Load**: Data automatically loaded on server startup
- **Graceful Shutdown**: Data saved when server receives Ctrl+C

## Response Status Codes

| Status | Description |
|--------|-------------|
| `Success` | Operation completed successfully |
| `Error` | Operation failed with error message |
| `Data` | Query returned data |
| `Stats` | Statistics response |
| `Similar` | Similarity search results |
| `Anomalies` | Anomaly detection results |
| `Motifs` | Motif discovery results |
| `SeriesList` | List of all series |
| `SeriesExport` | Exported series data |
| `Pong` | Ping response |

## Architecture

```
┌─────────────────────────────────────────┐
│           TSDB Server                   │
│  ┌─────────────────────────────────┐    │
│  │   TCP Listener (CLI & JSON)     │    │
│  └─────────────────────────────────┘    │
│              ▼                          │
│  ┌─────────────────────────────────┐    │
│  │   Command Parser                │    │
│  │   (CLI ↔ JSON)                  │    │
│  └─────────────────────────────────┘    │
│              ▼                          │
│  ┌─────────────────────────────────┐    │
│  │   Time Series Engine            │    │
│  │   • Vector Storage              │    │
│  │   • Similarity Search           │    │
│  │   • Matrix Profile              │    │
│  └─────────────────────────────────┘    │
│              ▼                          │
│  ┌─────────────────────────────────┐    │
│  │   Persistence Layer             │    │
│  │   (JSON File Storage)           │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## License

MIT License
