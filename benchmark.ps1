# TSDB Performance Benchmark Script
# Tests INSERT, QUERY, SIMILAR, ANOMALY, and MOTIF performance

$serverAddress = "127.0.0.1"
$serverPort = 9999

function Send-TsdbCommand {
    param([string]$json)
    $client = New-Object System.Net.Sockets.TcpClient($serverAddress, $serverPort)
    $stream = $client.GetStream()
    $writer = New-Object System.IO.StreamWriter($stream)
    $reader = New-Object System.IO.StreamReader($stream)
    
    $writer.WriteLine($json)
    $writer.Flush()
    $response = $reader.ReadLine()
    
    $client.Close()
    return $response
}

Write-Host "=========================================="
Write-Host "   TSDB PERFORMANCE BENCHMARK"
Write-Host "=========================================="
Write-Host ""

# Create benchmark series
Write-Host "[1] Creating benchmark series (dimension=8)..."
$result = Send-TsdbCommand '{"type":"CreateSeries","data":{"name":"benchmark","dimension":8}}'
Write-Host "    Result: $result"
Write-Host ""

# Benchmark INSERT
Write-Host "[2] INSERT Benchmark - 1000 data points..."
$insertTimes = @()
$sw = [System.Diagnostics.Stopwatch]::new()

for ($i = 0; $i -lt 1000; $i++) {
    $values = @()
    for ($j = 0; $j -lt 8; $j++) {
        $values += [math]::Round((Get-Random -Minimum 0.0 -Maximum 100.0), 2)
    }
    $valuesStr = $values -join ","
    $json = "{`"type`":`"Insert`",`"data`":{`"series`":`"benchmark`",`"values`":[$valuesStr]}}"
    
    $sw.Restart()
    $result = Send-TsdbCommand $json
    $sw.Stop()
    $insertTimes += $sw.Elapsed.TotalMilliseconds
    
    if (($i + 1) % 200 -eq 0) {
        Write-Host "    Inserted $($i + 1) points..."
    }
}

$avgInsert = ($insertTimes | Measure-Object -Average).Average
$minInsert = ($insertTimes | Measure-Object -Minimum).Minimum
$maxInsert = ($insertTimes | Measure-Object -Maximum).Maximum
$totalInsert = ($insertTimes | Measure-Object -Sum).Sum

Write-Host ""
Write-Host "    INSERT Results:"
Write-Host "    - Total time: $([math]::Round($totalInsert, 2)) ms"
Write-Host "    - Avg per insert: $([math]::Round($avgInsert, 3)) ms"
Write-Host "    - Min: $([math]::Round($minInsert, 3)) ms"
Write-Host "    - Max: $([math]::Round($maxInsert, 3)) ms"
Write-Host "    - Throughput: $([math]::Round(1000 / ($totalInsert / 1000), 2)) inserts/sec"
Write-Host ""

# Benchmark QUERY
Write-Host "[3] QUERY Benchmark - 10 queries..."
$queryTimes = @()

for ($i = 0; $i -lt 10; $i++) {
    $sw.Restart()
    $result = Send-TsdbCommand '{"type":"Query","data":{"series":"benchmark"}}'
    $sw.Stop()
    $queryTimes += $sw.Elapsed.TotalMilliseconds
}

$avgQuery = ($queryTimes | Measure-Object -Average).Average
Write-Host "    QUERY Results:"
Write-Host "    - Avg query time: $([math]::Round($avgQuery, 3)) ms"
Write-Host ""

# Benchmark SIMILAR
Write-Host "[4] SIMILAR Benchmark - 50 similarity searches..."
$similarTimes = @()

for ($i = 0; $i -lt 50; $i++) {
    $values = @()
    for ($j = 0; $j -lt 8; $j++) {
        $values += [math]::Round((Get-Random -Minimum 0.0 -Maximum 100.0), 2)
    }
    $valuesStr = $values -join ","
    $json = "{`"type`":`"FindSimilar`",`"data`":{`"series`":`"benchmark`",`"vector`":[$valuesStr],`"limit`":10,`"threshold`":0.0}}"
    
    $sw.Restart()
    $result = Send-TsdbCommand $json
    $sw.Stop()
    $similarTimes += $sw.Elapsed.TotalMilliseconds
}

$avgSimilar = ($similarTimes | Measure-Object -Average).Average
Write-Host "    SIMILAR Results:"
Write-Host "    - Avg search time: $([math]::Round($avgSimilar, 3)) ms"
Write-Host "    - Throughput: $([math]::Round(1000 / $avgSimilar, 2)) searches/sec"
Write-Host ""

# Benchmark STATS
Write-Host "[5] STATS Benchmark - 50 stats queries..."
$statsTimes = @()

for ($i = 0; $i -lt 50; $i++) {
    $sw.Restart()
    $result = Send-TsdbCommand '{"type":"GetStats","data":{"series":"benchmark"}}'
    $sw.Stop()
    $statsTimes += $sw.Elapsed.TotalMilliseconds
}

$avgStats = ($statsTimes | Measure-Object -Average).Average
Write-Host "    STATS Results:"
Write-Host "    - Avg stats time: $([math]::Round($avgStats, 3)) ms"
Write-Host ""

# Benchmark ANOMALY
Write-Host "[6] ANOMALY Benchmark - 10 anomaly detections..."
$anomalyTimes = @()

for ($i = 0; $i -lt 10; $i++) {
    $sw.Restart()
    $result = Send-TsdbCommand '{"type":"Anomaly","data":{"series":"benchmark","window":10,"k":5}}'
    $sw.Stop()
    $anomalyTimes += $sw.Elapsed.TotalMilliseconds
}

$avgAnomaly = ($anomalyTimes | Measure-Object -Average).Average
Write-Host "    ANOMALY Results:"
Write-Host "    - Avg detection time: $([math]::Round($avgAnomaly, 3)) ms"
Write-Host ""

# Benchmark MOTIF
Write-Host "[7] MOTIF Benchmark - 10 motif discoveries..."
$motifTimes = @()

for ($i = 0; $i -lt 10; $i++) {
    $sw.Restart()
    $result = Send-TsdbCommand '{"type":"Motif","data":{"series":"benchmark","window":10,"k":5}}'
    $sw.Stop()
    $motifTimes += $sw.Elapsed.TotalMilliseconds
}

$avgMotif = ($motifTimes | Measure-Object -Average).Average
Write-Host "    MOTIF Results:"
Write-Host "    - Avg discovery time: $([math]::Round($avgMotif, 3)) ms"
Write-Host ""

# Summary
Write-Host "=========================================="
Write-Host "   BENCHMARK SUMMARY"
Write-Host "=========================================="
Write-Host ""
Write-Host "| Operation  | Avg Time (ms) | Throughput    |"
Write-Host "|------------|---------------|---------------|"
Write-Host "| INSERT     | $([math]::Round($avgInsert, 3).ToString().PadLeft(13)) | $([math]::Round(1000 / $avgInsert, 0).ToString().PadLeft(8)) ops/s |"
Write-Host "| QUERY      | $([math]::Round($avgQuery, 3).ToString().PadLeft(13)) | -             |"
Write-Host "| SIMILAR    | $([math]::Round($avgSimilar, 3).ToString().PadLeft(13)) | $([math]::Round(1000 / $avgSimilar, 0).ToString().PadLeft(8)) ops/s |"
Write-Host "| STATS      | $([math]::Round($avgStats, 3).ToString().PadLeft(13)) | $([math]::Round(1000 / $avgStats, 0).ToString().PadLeft(8)) ops/s |"
Write-Host "| ANOMALY    | $([math]::Round($avgAnomaly, 3).ToString().PadLeft(13)) | $([math]::Round(1000 / $avgAnomaly, 0).ToString().PadLeft(8)) ops/s |"
Write-Host "| MOTIF      | $([math]::Round($avgMotif, 3).ToString().PadLeft(13)) | $([math]::Round(1000 / $avgMotif, 0).ToString().PadLeft(8)) ops/s |"
Write-Host ""
Write-Host "Data points in benchmark series: 1000"
Write-Host "Vector dimension: 8"
Write-Host ""
