/* onewire.i */
%module _onewire
%{
/* Put header files here (optional) */
  typedef unsigned char  uchar;


%}

%include typemaps.i

/* Network Management */

extern int   owAcquire(int portnum, char *port_zstr);
extern void  owRelease(int portnum);

extern int owSpeed(int portnum, int new_speed);

/* Button Management */

extern int   owFirst(int portnum, int do_reset, int alarm_only);
extern int   owNext(int portnum, int do_reset, int alarm_only);


%typemap(python,argout) uchar *serialnum_buf {
  $target = Py_BuildValue("s#",$source, 8);
}

%typemap(python,in) uchar *serialnum_buf {
  if (!PyString_Check($source)) {
    PyErr_SetString(PyExc_TypeError,"not a string");
    return NULL;
  }
  $target = PyString_AsString($source);
}

extern void  owSerialNum(int portnum, uchar *serialnum_buf, int do_read);
extern void  PrintSerialNum(uchar *serialnum_buf);
extern int owAccess(int portnum);
extern int owOverdriveAccess(int portnum);
extern int owVerify(int portnum, int alarm_only);

%typemap(python,in) uchar *INSNum {
  if (!PyString_Check($source)) {
    PyErr_SetString(PyExc_TypeError,"not a string");
    return NULL;
  }
  $target = PyString_AsString($source);
}
extern char *owGetName(uchar *INSNum);
extern char *owGetDescription(uchar *INSNum);


/* File Management */

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

%typemap(python,out) DirectoryPath {
  int i, j;
  if ($source) {
    for(i=0;i<$source->NumEntries;i++)
      {
	for(j=0;j<4;j++)
	  printf("%c",$source->Entries[i][j]);
	printf("/");
      }
    $target = Py_BuildValue("{siss#s{}}",
			    "NumEntries",$source->NumEntries,
			    "Ref",$source->Entries,1,
			    "Entries");
    free($source);
  }
}

%typemap(python, in) DirectoryPath *CDBuf {
  PyObject *value;
  int i;

  $target = malloc(sizeof(DirectoryPath));

  if(!PyDict_Check($source)) {
    PyErr_SetString(PyExc_TypeError,"not a dictionary");
    free($target);
    return NULL;
  }
  value = PyDict_GetItem($source, Py_BuildValue("s","Ref"));
  if(value)  $target->Ref = PyString_AsString(value)[0];
  else {
    PyErr_SetString(PyExc_TypeError,"dictionary has missing Ref key");  
    free($target);
    return NULL;
  }

  value = PyDict_GetItem($source, Py_BuildValue("s","Entries"));
  if(value) {
     $target->NumEntries = PyList_Size(value);
    if ( $target->NumEntries > 10) {
      PyErr_SetString(PyExc_ValueError,"Too many Entries (max 10)");  
      free($target);
      return NULL;
    } else {
      for (i=0; i<$target->NumEntries; i++) {
	strncpy($target->Entries[i],PyString_AsString(PyList_GetItem(value,i)),4);
      }
    }
  }
  else {
    PyErr_SetString(PyExc_TypeError,"dictionary has missing Entries key");  
    free($target);
    return NULL;
  }
}

extern DirectoryPath owGetCurrentDir(int portnum, uchar *INSNum);
extern int owChangeDirectory(int portnum, uchar *INSNum, DirectoryPath *CDBuf);

%typemap(python,argout) FileEntry *FE {
  if ($source) {
    if ($source->Name[0]) {
      $target = Py_BuildValue("{ss#sisisisiss#}",
			      "Name",$source->Name,4,
			      "Ext",$source->Ext,
			      "Spage",$source->Spage,
			      "NumPgs",$source->NumPgs,
			      "Attrib",$source->Attrib,
			      "BM",$source->BM,32);
    } else {
      $target =  Py_BuildValue("");
    }
    free($source);
  }
}

%typemap(python,in) FileEntry *FE {
  PyObject *value;

  $target = malloc(sizeof(FileEntry));
 
  if(PyDict_Check($source)) {
    
    value = PyDict_GetItem($source, Py_BuildValue("s","Name"));
    if(value) strncpy($target->Name,PyString_AsString(value),4);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($target);
      return NULL;
    }
    
    value = PyDict_GetItem($source, Py_BuildValue("s","Ext"));
    if(value) $target->Ext = PyInt_AsLong(value);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($target);
      return NULL;
    }
  }
}



extern int owFirstFile(int portnum, uchar *INSNum, FileEntry *FE);
extern int owNextFile(int portnum, uchar *INSNum, FileEntry *FE);

%typemap(python,argout) short OUThnd {  $target = Py_BuildValue("i",$source); }
%typemap(python,ignore) short OUThnd {}

extern int owOpenFile(int portnum, uchar *INSNum, FileEntry *FE, %val short *OUThnd);

%typemap(python,ignore) uchar *buf { $target = malloc(65536);}
%typemap(python,argout) uchar *buf { };
%typemap(python,ignore) int maxlen { $target = 65536; } 
%typemap(python,ignore) int OUTfl_len {}

%{
 PyObject *owMyReadFile(int portnum, uchar *INSNum, short hnd, uchar *buf, int maxlen, int *OUTfl_len) {
   if(owReadFile(portnum, INSNum, hnd, buf, maxlen, OUTfl_len))
     return Py_BuildValue("s#",buf,*OUTfl_len);
   else
     return Py_BuildValue("");
 }
%}

PyObject *owMyReadFile(int portnum, uchar *INSNum, short hnd, uchar *buf, int maxlen, %val int *OUTfl_len);
//int owReadFile(int portnum, uchar *INSNum, short hnd, uchar *buf, int maxlen, %val int *OUTfl_len);
int owCloseFile(int portnum, uchar *INSNum, short hnd);

%typemap(python,ignore) int maxwrite {}

%typemap(python,in) FileEntry *INFE {
  PyObject *value;

  $target = malloc(sizeof(FileEntry));
 
  if(PyDict_Check($source)) {
    
    value = PyDict_GetItem($source, Py_BuildValue("s","Name"));
    if(value) strncpy($target->Name,PyString_AsString(value),4);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($target);
      return NULL;
    }
    
    value = PyDict_GetItem($source, Py_BuildValue("s","Ext"));
    if(value) $target->Ext = PyInt_AsLong(value);
    else {
      PyErr_SetString(PyExc_TypeError,"dictionary has missing Name key");  
      free($target);
      return NULL;
    }
  }
}

int owCreateFile(int portnum, uchar *INSNum, %val int *maxwrite, %val short *OUThnd,  FileEntry *INFE);
int owDeleteFile(int portnum, uchar *INSNum, FileEntry *FE);

%typemap(python,in) uchar *INbuf {
  if (!PyString_Check($source)) {
    PyErr_SetString(PyExc_TypeError,"not a string");
    return NULL;
  }
  $target = PyString_AsString($source);
}

int owWriteFile(int portnum, uchar *INSNum, short hnd, uchar *INbuf, int len);

// extern int owReadFile(int portnum, uchar *SNum, short hnd, uchar *buf, int maxlen, int *fl_len)
/* Error handling */
extern int owGetErrorNum(void);
extern void owClearError(void);
extern int owHasErrors(void);
extern void owRaiseError(int);
extern void owPrintErrorMsgStd();
extern uchar *owGetErrorMsg(int);
