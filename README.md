# Finance App
個人製作的簡易看盤軟體

操作方式：

可在`stocks.json`中新增標籤、標的，請注意這邊是從yahoo finance搜尋，所以標的號碼必須依照yahoo的格式。

此軟體是透過streamlit製作，所以需要先下載python以及`requirements.txt`中的套件，請先確認自己電腦中是否有python以及pip，目前python3.8以上皆可操作。

```pip install -r requirements.txt```

下載完畢後，確認是否可以使用streamlit
測試streamlit：`streamlit --version`，應該會回傳以下資訊：`Streamlit, version 1.57.0`

使用streamlit：
```
/> streamlit run app.py
2026-05-29 10:53:32.132 Uvicorn server started on 0.0.0.0:8501

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://X.X.X.X:8501
```
通常預設port是8501，當然可以自行修改
```
streamlit run app.py --server.port [port number]
```
