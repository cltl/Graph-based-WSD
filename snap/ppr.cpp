#include <Python.h>
#include <Snap.h>
#include <chrono>
#include <set>

typedef struct {
    PyObject_HEAD
        PNGraph Graph;
} snap_Graph;


static PyObject * Snap_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    snap_Graph *self;
    self = (snap_Graph*)type->tp_alloc(type, 0);
    return (PyObject *)self;
}

static int Snap_init(snap_Graph *self, PyObject *args, PyObject *kwds) {
    const char *path;
    if (!PyArg_ParseTuple(args, "s", &path))
        return -1;

    // Load a directed graph
    self->Graph = TSnap::LoadEdgeList<PNGraph>(TStr(path));
    return 0;
}

//Return the number of nodes in the graph
static PyObject *snap_getNNodes(PyObject *self, PyObject *args) {
    PNGraph g = ((snap_Graph*)self)->Graph;
    return PyLong_FromLong(g->GetNodes());
}

//Return the number of edges in the graph
static PyObject *snap_getNEdges(PyObject *self, PyObject *args) {
    PNGraph g = ((snap_Graph*)self)->Graph;
    return PyLong_FromLong(g->GetEdges());
}

//Add a node
static PyObject *snap_addNode(PyObject *self, PyObject *args) {
    long nodeid;
    if (!PyArg_ParseTuple(args, "l", &nodeid))
        return NULL;
    PNGraph g = ((snap_Graph*)self)->Graph;
    g->AddNode(nodeid);
    return PyBool_FromLong(1);
}

//Add an edge
static PyObject *snap_addEdge(PyObject *self, PyObject *args) {
    long source, dest;
    if (!PyArg_ParseTuple(args, "ll", &source, &dest))
        return NULL;
    PNGraph g = ((snap_Graph*)self)->Graph;
    g->AddEdge(source, dest);
    return PyBool_FromLong(1);
}


template<class PGraph>
void GetPersPageRank(const PGraph& Graph,
        TIntFltH& PRankH,
        const double& C,
        const double& Eps,
        const int& MaxIter,
        std::vector<int> &startNodes) {

    std::set<int> s_startNodes;
    for(auto el : startNodes) {
        s_startNodes.insert(el);
    }

    const int NNodes = Graph->GetNodes();
    TVec<typename PGraph::TObj::TNodeI> NV;
    PRankH.Gen(NNodes);
    int MxId = -1;
    for (typename PGraph::TObj::TNodeI NI = Graph->BegNI(); NI < Graph->EndNI(); NI++) {
        NV.Add(NI);
        PRankH.AddDat(NI.GetId(), 0);
        int Id = NI.GetId();
        if (Id > MxId) {
            MxId = Id;
        }
    }

    TFltV PRankV(MxId+1);
    TIntV OutDegV(MxId+1);

    for (int j = 0; j < NNodes; j++) {
        typename PGraph::TObj::TNodeI NI = NV[j];
        int Id = NI.GetId();
        if (s_startNodes.count(Id)) {
            PRankV[Id] = 1.0 / startNodes.size();
        }  else {
            PRankV[Id] = 0;
        }
        //PRankV[Id] = 1.0 / NNodes;
        OutDegV[Id] = NI.GetOutDeg();
    }

    TFltV TmpV(NNodes);

    for (int iter = 0; iter < MaxIter; iter++) {
        for (int j = 0; j < NNodes; j++) {
            typename PGraph::TObj::TNodeI NI = NV[j];
            TFlt Tmp = 0;
            for (int e = 0; e < NI.GetInDeg(); e++) {
                const int InNId = NI.GetInNId(e);
                const int OutDeg = OutDegV[InNId];
                if (OutDeg > 0) {
                    Tmp += PRankV[InNId] / OutDeg;
                }
            }
            TmpV[j] =  C*Tmp; // Berkhin (the correct way of doing it)
        }
        double sum = 0;
        for (int i = 0; i < TmpV.Len(); i++) { sum += TmpV[i]; }
        const double Leaked = (1.0-sum) / double(NNodes);

        double diff = 0;
        for (int i = 0; i < NNodes; i++) {
            typename PGraph::TObj::TNodeI NI = NV[i];
            double NewVal = TmpV[i] + Leaked; // Berkhin
            int Id = NI.GetId();
            diff += fabs(NewVal-PRankV[Id]);
            PRankV[Id] = NewVal;
        }
        if (diff < Eps) { break; }
    }

    for (int i = 0; i < NNodes; i++) {
        typename PGraph::TObj::TNodeI NI = NV[i];
        PRankH[i] = PRankV[NI.GetId()];
    }
}

//Launch PPR
static PyObject *snap_ppr(PyObject *self, PyObject *args, PyObject *kw) {
    auto start = std::chrono::high_resolution_clock::now();

    PNGraph g = ((snap_Graph*)self)->Graph;
    TIntFltH ranks;
    //Get Parameters
    double C = 0.85;
    long maxiter = 100;
    double eps = 0.0001;
    static const char *kwlist[5] = { "", "C", "eps", "maxiter", NULL };
    PyObject *i_startNodes;
    std::vector<int> startNodes;
    if (!PyArg_ParseTupleAndKeywords(args, kw,
                "O!|ddl",
                (char **) kwlist,
                &PyList_Type,
                &i_startNodes,
                &C,
                &eps, &maxiter)) {
        return NULL;
    }

    //Parse the list of initial nodes
    for(int i = 0; i < PyList_Size(i_startNodes); ++i) {
        PyObject *el = PyList_GetItem(i_startNodes, i);
        if (!PyLong_Check(el)) {
            std::cerr << "Not a long value" << std::endl;
        }
        long v = PyLong_AsLongLong(el);
        startNodes.push_back(v);
    }

    std:: cout << "Executing PPR with C=" << C << " eps=" << eps << " maxiter=" << maxiter << " ..." << std::endl;

    GetPersPageRank<PNGraph>(g, ranks, C, eps, maxiter, startNodes);

    PyObject *obj = PyList_New(0);
    for(auto NI = g->BegNI(); NI < g->EndNI(); NI++) {
        const long NId = NI.GetId();
        PyObject *t = PyTuple_New(2);
        PyTuple_SetItem(t, 0, PyLong_FromLong(NId));
        PyTuple_SetItem(t, 1, PyFloat_FromDouble(ranks.GetDat(NId)));
        PyList_Append(obj, t);
        Py_DECREF(t);
    }

    auto elapsed = std::chrono::high_resolution_clock::now() - start;
    std::cout << "Time exec: " << std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count() << " milliseconds" << std::endl;
    return obj;
}

static void Snap_dealloc(snap_Graph* self) {
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyMethodDef Snap_methods[] = {
    {"GetNNodes", snap_getNNodes, METH_VARARGS, "Get the number of nodes in the graph" },
    {"GetNEdges", snap_getNEdges, METH_VARARGS, "Get the number of edges in the graph" },
    {"AddNode", snap_addNode, METH_VARARGS, "Add a node to the graph" },
    {"AddEdge", snap_addEdge, METH_VARARGS, "Add an edge to the graph" },
    {"PPR", (PyCFunction)snap_ppr, METH_VARARGS | METH_KEYWORDS, "Launch PPR" },
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static PyTypeObject snap_GraphType = {
    PyVarObject_HEAD_INIT(NULL, 0)
        "ppr.Graph",             /* tp_name */
    sizeof(snap_Graph),             /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)Snap_dealloc, /* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_reserved */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    0,                         /* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash  */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
        Py_TPFLAGS_BASETYPE,   /* tp_flags */
    "SNAP Graph",           /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    Snap_methods,             /* tp_methods */
    0,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Snap_init,      /* tp_init */
    0,                         /* tp_alloc */
    Snap_new,                 /* tp_new */
};


static struct PyModuleDef snapmodule = {
    PyModuleDef_HEAD_INIT,
    "ppr",   /* name of module */
    NULL,        /* module documentation, may be NULL */
    -1,          /* size of per-interpreter state of the module,
                    or -1 if the module keeps state in global variables. */
    NULL
};

PyMODINIT_FUNC PyInit_ppr(void) {
    PyObject *m;
    snap_GraphType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&snap_GraphType) < 0)
        return NULL;
    m = PyModule_Create(&snapmodule);
    if (m == NULL)
        return NULL;
    Py_INCREF(&snap_GraphType);
    PyModule_AddObject(m, "Graph", (PyObject *)&snap_GraphType);
    return m;
}
