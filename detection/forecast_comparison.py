actual = 47
ewma = 54.83
arima = 44.91

ewma_error = abs(actual - ewma)
arima_error = abs(actual - arima)

print("EWMA Error:", round(ewma_error, 2))
print("ARIMA Error:", round(arima_error, 2))

if ewma_error < arima_error:
    print("Better Model: EWMA")
else:
    print("Better Model: ARIMA")