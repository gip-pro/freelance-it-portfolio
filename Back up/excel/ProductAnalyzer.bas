Attribute VB_Name = "ProductAnalyzer"
Option Explicit

Private Const API_URL As String = "http://localhost:8000/analyze-product"
Private Const PROFIT_MARGIN As Double = 0.3

Public Sub AnalyzeProduct()
    On Error GoTo ErrorHandler

    Dim imageUrl As String
    imageUrl = Trim(Range("A2").Value)

    If imageUrl = "" Then
        MsgBox "Image URL is empty", vbExclamation
        Exit Sub
    End If

    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")

    Dim body As String
    body = "{""image_url"":""" & imageUrl & """}"

    http.Open "POST", API_URL, False
    http.setRequestHeader "Content-Type", "application/json"
    http.Send body

    If http.Status <> 200 Then
        MsgBox "API Error: " & http.responseText, vbCritical
        Exit Sub
    End If

    Dim json As Object
    Set json = JsonConverter.ParseJson(http.responseText)

    Dim marketPrice As Double
    marketPrice = CDbl(json("estimated_market_price"))

    Dim confidence As Double
    confidence = CDbl(json("confidence"))

    If marketPrice <= 0 Or confidence < 0 Or confidence > 1 Then
        MsgBox "Invalid data received", vbCritical
        Exit Sub
    End If

    Dim maxCost As Double
    maxCost = marketPrice * (1 - PROFIT_MARGIN)

    Range("B2").Value = json("product_name")
    Range("C2").Value = json("category")
    Range("D2").Value = marketPrice
    Range("E2").Value = confidence
    Range("F2").Value = maxCost

    MsgBox "Success", vbInformation
    Exit Sub

ErrorHandler:
    MsgBox "Unexpected error: " & Err.Description, vbCritical
End Sub