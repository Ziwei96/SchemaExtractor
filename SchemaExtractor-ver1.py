from werkzeug.wrappers import response
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
import pandas as pd
import pdfplumber
import xml.etree.ElementTree as ET
from pandas.core.frame import DataFrame

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])

def index():
  if request.method == 'POST':
    ifile = request.files['csv_file']
    Separator=request.form['separator']
    skip_rows=request.form['skip_rows']
    
    obj = request.files.get('csv_file')
    filename = secure_filename(obj.filename)
    #print(filename)

    df_file = pd.DataFrame([])
    df = pd.DataFrame([])

    if filename.endswith('.csv'):
        df_file = pd.read_csv(ifile, sep=Separator, low_memory=False, skiprows=int(skip_rows), encoding='unicode_escape')
        
        df = df_handler(df_file,filename)
    
    if filename.endswith('.psv'):
        df_file  =  pd.read_csv(ifile, sep=Separator, low_memory=False, skiprows=int(skip_rows), encoding='unicode_escape')
        df = df_handler(df_file,filename)

    if filename.endswith('.xlsx'):
        df_file  = pd.read_excel(ifile)
        df = df_handler(df_file,filename)
    
    if filename.endswith('.xls'):
        df_file  = pd.read_excel(ifile) 
        df = df_handler(df_file,filename)

    if filename.endswith('.xml'):
        xml_data = ifile.read()  # Read file
        root = ET.XML(xml_data)  # Parse XML
        #print(type(root))
        data = []
        cols = []
        for i, child in enumerate(root):
            data.append([subchild.text for subchild in child])
            cols.append(child.tag)

        #print(data)
        #print(cols)
        df = xml_handler(root,data,cols)

    if filename.endswith('.pdf'):
        pdf = pdfplumber.open(ifile)
        table = pd.DataFrame([])
        for page in pdf.pages:
            row = page.extract_text().split('\n')
            table_page = []
            for words in row:
                s = []
                for word in words.split():
                    if word.isdigit():
                        s.append(int(word))
                    elif IsFloatNum(word):
                        s.append(float(word))
                    else:
                        s.append(word)
                table_page.append(s)

            table_df = pd.DataFrame(table_page)
            table = pd.concat([table,table_df], axis=1,ignore_index=True)
            #print(table)

        df = pdf_handler(table,filename)
    
    output = BytesIO()
    with pd.ExcelWriter(output) as writer:
      #writer.book = openpyxl.load_workbook(writer, sheet_name='schema1')
      df.to_excel(writer, index=False) 
      #writer.close()
    output.seek(0)
    #wb = openpyxl.Workbook()
    #ws = wb.active
    
    #for i, xpath in enumerate(xpaths):    #(flattened_xpaths):
    #    ws.cell(row=i+1, column=1, value=xpath)
    
    #wb.save(filename="outputfile.xlsx")

    fileNamePre = filename.split('.')[0]
    #extention = filename.split('.')[1]
    name_fin = fileNamePre + '_schema.xlsx'
    #print(name_fin)

    response = send_file(output,download_name = name_fin,
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          as_attachment=True)
    return response

  return '''
    <!doctype html>
    <html>
      <body>
        <h1>Upload a file</h1>
        <form method="post" enctype="multipart/form-data">
          <input type="file" name="csv_file">
          <label for="Separator">Separator: </label>
          <input type="text" id="Separator" name="separator">
          <label for="skip_rows">No. of Rows to Skip</label>
          <input type="text" id="skip_rows" name="skip_rows">
          <input type="submit" value="Upload">
        </form>
      </body>
    </html>
  '''

def IsFloatNum(str):
  s=str.split('.')
  if len(s)>2:
    return False
  else:
    for si in s:
      if not si.isdigit():
        return False
    return True

def df_handler(df_file,filename):
    # Change the read parameters based on input files

    columnNames = list(df_file.columns)
    columnNames = columnNames[1:]
    columnDataTypes = list(df_file.dtypes)
    columnDataTypes = columnDataTypes[1:]
    # -----------Replace Datatypes---------------------
    for x in range(len(columnDataTypes)):
      if columnDataTypes[x] == "object":
        columnDataTypes[x] = 'string'
      if columnDataTypes[x] == "float64":
        columnDataTypes[x] = 'float'
      if columnDataTypes[x] == "int64":
        columnDataTypes[x] = 'int'
      # ---------Make Dataframe---------
    df = pd.DataFrame([])
    df['Grouping'] = [' ' for i in range(len(columnNames))]
    df['File_Name'] = [filename for i in range(len(columnNames))]
    df['attributeID'] = range(1, len(columnNames) + 1)
    df['attributeName'] = columnNames
    df['attributeDescription'] = [' ' for i in range(len(columnNames))]
    df['Type'] = columnDataTypes

    #print(df)
    return df

def pdf_handler(df_file,filename):
    #write pdf to xlsx
    # Change the read parameters based on input files

    columnNames = list(df_file.iloc[0])
    #columnNames = columnNames[1:]
    print(columnNames)
    columnDataTypes = list(df_file.dtypes)
    #columnDataTypes = columnDataTypes[1:]
      # -----------Replace Datatypes---------------------
    for x in range(len(columnDataTypes)):
      if columnDataTypes[x] == "object":
        columnDataTypes[x] = 'string'
      if columnDataTypes[x] == "float64":
        columnDataTypes[x] = 'float'
      if columnDataTypes[x] == "int64":
        columnDataTypes[x] = 'int'
      # ---------Make Dataframe---------
    df = pd.DataFrame([])
    df['Grouping'] = [' ' for i in range(len(columnNames))]
    df['File_Name'] = [filename for i in range(len(columnNames))]
    df['attributeID'] = range(1, len(columnNames) + 1)
    df['attributeName'] = columnNames
    df['attributeDescription'] = [' ' for i in range(len(columnNames))]
    df['Type'] = columnDataTypes

    #print(df)
    return df

def xml_handler(root,data,cols):
    #write xml to xlsx
    for i, child in enumerate(root):
      data.append([subchild.text for subchild in child])
      cols.append(child.tag)

    df = pd.DataFrame(data).T  # Write in DF and transpose it
    df.columns = cols  # Update column names
    #print(df)
    
    return df


if __name__ == '__main__':
  app.run(debug=True,host='0.0.0.0')
