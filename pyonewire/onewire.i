/* onewire.i */
%module onewire
%{
  typedef unsigned char  uchar;
%}

// 
// structs
//

%{

typedef struct
{
   uchar NumEntries;      // number of entries in path 0-10 
   char  Ref;             // reference character '\' or '.' 
   char  Entries[10][4];  // sub-directory entry names
} DirectoryPath;

typedef struct 
{
   uchar Name[4];          // 4
   uchar Ext;              // 1
   uchar Spage;            // 1
   uchar NumPgs;           // 1
   uchar Attrib;           // 1
   uchar BM[32];           // 32
} FileEntry;

%}

// 
// typemaps
//

%typemap(python,argout) uchar *serialnum_buf {
   $result = Py_BuildValue("s#",$1, 8);
}


%typemap(python,in) uchar * {
   if (!PyString_Check($input)) {
      PyErr_SetString(PyExc_TypeError,"serialnum not a string");
      return NULL;
   }
   $1 = PyString_AsString($input);
}

// for therm10.h
//%typemap(python,in) uchar *serialnum_buf = uchar *SerialNum;
//%typemap(python,argout) float * { $result = Py_BuildValue("f",$1); }

%typemap(python,in,numinputs=0) float *Temp (float temp) {
   $1 = &temp;
}
%typemap(python,argout) float * { 
   $result = PyFloat_FromDouble(*$1);
}

%typemap(python,in) uchar *INSNum {
   if (!PyString_Check($input)) {
      PyErr_SetString(PyExc_TypeError,"insnum not a string");
      return NULL;
   }
   $1 = PyString_AsString($input);
}

%typemap(python,out) DirectoryPath {
   int i, j;
   DirectoryPath *tmp = &$1;
   if (tmp) {
      for(i=0;i<tmp->NumEntries;i++)
      {
         for(j=0;j<4;j++)
            printf("%c",tmp->Entries[i][j]);
         printf("/");
      }
      $result = Py_BuildValue("{siss#s{}}",
      "NumEntries",tmp->NumEntries,
      "Ref",tmp->Entries,1,
      "Entries");
      free(tmp);
   }
}

%typemap(python, in) DirectoryPath *CDBuf {
  PyObject *value;
  int i;

  $1 = malloc(sizeof(DirectoryPath));

  if(!PyDict_Check($input)) {
    PyErr_SetString(PyExc_TypeError,"not a dictionary");
    free($1);
    return NULL;
  }
  value = PyDict_GetItem($input, Py_BuildValue("s","Ref"));
  if(value)  $1->Ref = PyString_AsString(value)[0];
  else {
    PyErr_SetString(PyExc_TypeError,"dictionary has missing Ref key");  
    free($1);
    return NULL;
  }

  value = PyDict_GetItem($input, Py_BuildValue("s","Entries"));
  if(value) {
     $1->NumEntries = PyList_Size(value);
    if ( $1->NumEntries > 10) {
      PyErr_SetString(PyExc_ValueError,"Too many Entries (max 10)");  
      free($1);
      return NULL;
    } else {
      for (i=0; i<$1->NumEntries; i++) {
         strncpy($1->Entries[i],PyString_AsString(PyList_GetItem(value,i)),4);
      }
    }
  }
  else {
    PyErr_SetString(PyExc_TypeError,"dictionary has missing Entries key");  
    free($1);
    return NULL;
  }
}

%typemap(python,argout) FileEntry *FE {
  if ($1) {
    if ($1->Name[0]) {
      $result = Py_BuildValue("{ss#sisisisiss#}",
            "Name",$1->Name,4,
            "Ext",$1->Ext,
            "Spage",$1->Spage,
            "NumPgs",$1->NumPgs,
            "Attrib",$1->Attrib,
            "BM",$1->BM,32);
    } else {
      $result =  Py_BuildValue("");
    }
    free($1);
  }
}

%typemap(python,in) FileEntry *FE {
  PyObject *value;

  $1 = malloc(sizeof(FileEntry));
 
  if(PyDict_Check($input)) {
    
    value = PyDict_GetItem($input, Py_BuildValue("s","Name"));
    if(value) strncpy($1->Name,PyString_AsString(value),4);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($1);
      return NULL;
    }
    
    value = PyDict_GetItem($input, Py_BuildValue("s","Ext"));
    if(value) $1->Ext = PyInt_AsLong(value);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($1);
      return NULL;
    }
  }
}

//%typemap(python,in)     short *hnd (short temp_hnd) { $1 = &temp_hnd; }
// [mjw] made a few changes here; changed *OUThnd -> *hnd
%typemap(python,argout) short *hnd {  
   if ($1 != NULL)
      $result = Py_BuildValue("i",*$1);
   else 
      $result = Py_None;
   free($1);
}
%typemap(python,in,numinputs=0) short * { short *temp_hnd = malloc(sizeof(short)); $1 = temp_hnd; }
%typemap(python,argout) short * { free($1); }
%typemap(python,in,numinputs=0) int *maxwrite (int tempint) {$1 = &tempint;}

// [mjw] removed malloc here; added possibly unnecessary buildValue to the
// output
%typemap(python,in,numinputs=0) uchar *buf (uchar tmpbuf[65535]) { $1 = tmpbuf;}
%typemap(python,argout) uchar *buf { $result = Py_BuildValue("s",$1);};

// [mjw] the typmaps for owReadFile have been replaced; since they were just
// default values, they are handled in the owMyReadFile C.
//%typemap(python,ignore) int maxlen (int tempmaxlen) { tempmaxlen = 65536; $1 = tempmaxlen; } 
//%typemap(python,in) int maxlen (int tempmax) { tempmax = 32; } 
//%typemap(python,ignore) int maxlen { $1 = 32; } 
//%typemap(python,ignore) int *OUTfl_len {}

%{
 PyObject *owMyReadFile(int portnum, uchar *INSNum, short hnd, uchar *buf) {
   int fl_len= 0;
   int maxlen = 65535;
   if(owReadFile(portnum, INSNum, hnd, buf, maxlen, &fl_len))
     return Py_BuildValue("s#",buf,fl_len);
   else
     return Py_BuildValue("");
 }
%}

%{
  PyObject *myOwFirst(int portnum, int do_reset, int alarm_only) {
     int ret;
     Py_BEGIN_ALLOW_THREADS
     ret = owFirst(portnum,do_reset,alarm_only);
     Py_END_ALLOW_THREADS
     return Py_BuildValue("i",ret);
  }
  PyObject *myOwNext(int portnum, int do_reset, int alarm_only) {
     int ret;
     Py_BEGIN_ALLOW_THREADS
     ret = owNext(portnum,do_reset,alarm_only);
     Py_END_ALLOW_THREADS
     return Py_BuildValue("i",ret);
  }
%}

%typemap(python,in) FileEntry *INFE {
  PyObject *value;

  $1 = malloc(sizeof(FileEntry));
 
  if(PyDict_Check($input)) {
    
    value = PyDict_GetItem($input, Py_BuildValue("s","Name"));
    if(value) strncpy($1->Name,PyString_AsString(value),4);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($1);
      return NULL;
    }
    
    value = PyDict_GetItem($input, Py_BuildValue("s","Ext"));
    if(value) $1->Ext = PyInt_AsLong(value);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($1);
      return NULL;
    }
  }
}

%typemap(python,in) uchar *INbuf {
  if (!PyString_Check($input)) {
    PyErr_SetString(PyExc_TypeError,"not a string");
    return NULL;
  }
  $1 = PyString_AsString($input);
}

//
// functions
//

/* Network Management */

extern int   owAcquire(int portnum, char *port_zstr);
extern void  owRelease(int portnum);
extern int owSpeed(int portnum, int new_speed);

/* Button Management */

extern int   owFirst(int portnum, int do_reset, int alarm_only);
extern int   owNext(int portnum, int do_reset, int alarm_only);

extern void  owSerialNum(int portnum, uchar *serialnum_buf, int do_read);
extern void  PrintSerialNum(uchar *serialnum_buf);
extern int owAccess(int portnum);
extern int owOverdriveAccess(int portnum);
extern int owVerify(int portnum, int alarm_only);

/* File Management */

extern DirectoryPath owGetCurrentDir(int portnum, uchar *INSNum);
extern int owChangeDirectory(int portnum, uchar *INSNum, DirectoryPath *CDBuf);

extern int owFirstFile(int portnum, uchar *INSNum, FileEntry *FE);
extern int owNextFile(int portnum, uchar *INSNum, FileEntry *FE);

extern int owOpenFile(int portnum, uchar *INSNum, FileEntry *FE, short *hnd);
PyObject *owMyReadFile(int portnum, uchar *INSNum, short hnd, uchar *buf);
PyObject *myOwFirst(int,int,int);
PyObject *myOwNext(int,int,int);
int owCloseFile(int portnum, uchar *INSNum, short hnd);

//int owCreateFile(int portnum, uchar *INSNum, %val int *maxwrite, %val short *hnd,  FileEntry *INFE);
int owCreateFile(int portnum, uchar *INSNum, int *maxwrite, short *hnd,  FileEntry *INFE);
int owDeleteFile(int portnum, uchar *INSNum, FileEntry *FE);
int owWriteFile(int portnum, uchar *INSNum, short hnd, uchar *INbuf, int len);

/* Extra Features */

extern int ReadTemperature(int, uchar*, float*Temp);

/* Error handling */
extern int owGetErrorNum(void);
extern void owClearError(void);
extern int owHasErrors(void);
extern void owRaiseError(int);
extern void owPrintErrorMsgStd();
extern uchar *owGetErrorMsg(int);
