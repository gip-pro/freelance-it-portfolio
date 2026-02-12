Attribute VB_Name = "AnalyzeProduct"
Option Explicit

' Requires reference/module:
' 1) Import JsonConverter.bas from VBA-JSON (https://github.com/VBA-tools/VBA-JSON)
' 2) Add reference: Microsoft Scripting Runtime

Private Const API_URL As String = "http://localhost:8000/analyze-product"
Private Const MAX_COST_PERCENT As Double = 0.65 ' 65% of market price

Public Sub AnalyzeProductFromSheet()
    On Error GoTo ErrHandler

    Dim imageUrl As String
    imageUrl = Trim$(CStr(ActiveSheet.Range("A2").Value))

    If Len(imageUrl) = 0 Then
        ActiveSheet.Range("B2").Value = "Ошибка: пустой URL"
        Exit Sub
    End If

    Dim requestBody As String
    requestBody = "{""image_url"":""" & EscapeJson(imageUrl) & """}"

    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")

    http.Open "POST", API_URL, False
    http.setRequestHeader "Content-Type", "application/json"
    http.send requestBody

    If http.Status < 200 Or http.Status >= 300 Then
        ActiveSheet.Range("B2").Value = "HTTP error: " & http.Status
        ActiveSheet.Range("C2").Value = http.responseText
        Exit Sub
    End If

    Dim json As Object
    Set json = JsonConverter.ParseJson(http.responseText)

    If Not CBool(json("success")) Then
        ActiveSheet.Range("B2").Value = "API error"
        ActiveSheet.Range("C2").Value = CStr(json("error"))
        Exit Sub
    End If

    Dim data As Object
    Set data = json("data")

    Dim productName As String
    Dim category As String
    Dim marketPrice As Double
    Dim confidence As Double
    Dim maxAllowedCost As Double

    productName = CStr(data("product_name"))
    category = CStr(data("category"))
    marketPrice = CDbl(data("estimated_market_price"))
    confidence = CDbl(data("confidence"))

    maxAllowedCost = marketPrice * MAX_COST_PERCENT

    ' Output to cells
    ActiveSheet.Range("B2").Value = productName
    ActiveSheet.Range("C2").Value = category
    ActiveSheet.Range("D2").Value = marketPrice
    ActiveSheet.Range("E2").Value = confidence
    ActiveSheet.Range("F2").Value = maxAllowedCost

    Exit Sub

ErrHandler:
    ActiveSheet.Range("B2").Value = "VBA runtime error"
    ActiveSheet.Range("C2").Value = Err.Description
End Sub

Private Function EscapeJson(ByVal value As String) As String
    Dim result As String
    result = Replace(value, "\", "\\")
    result = Replace(result, """", "\"")
    result = Replace(result, vbCrLf, "\n")
    result = Replace(result, vbCr, "\n")
    result = Replace(result, vbLf, "\n")
    EscapeJson = result
End Function
