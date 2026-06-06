import subprocess
import sys
import os
import glob

# Try to find the teamspeak3 binary dynamically or fallback
TS3_BIN = "./result/opt/teamspeak/ts3client"
if len(sys.argv) > 1:
    TS3_BIN = sys.argv[1]
elif not os.path.exists(TS3_BIN):
    paths = glob.glob("/nix/store/*-teamspeak3-*/opt/teamspeak/ts3client")
    if paths:
        TS3_BIN = paths[0]
        print(f"Auto-detected Teamspeak binary: {TS3_BIN}")
    else:
        print(f"Warning: Teamspeak binary not found at {TS3_BIN} or in /nix/store. Make sure to pass it as an argument.")

def generate():
    print("Reading ELF symbols...")
    result = subprocess.run(['readelf', '-Ws', TS3_BIN], capture_output=True, text=True)
    
    manual_overrides = {
        "_ZN14QWebEngineViewC1EP7QWidget": ("QWebEngineView C1", "QWidget", "QWidget* parent"),
        "_ZN14QWebEngineViewC2EP7QWidget": ("QWebEngineView C2", "QWidget", "QWidget* parent"),
        "_ZN17QWebEngineProfileC1ERK7QStringP7QObject": ("QWebEngineProfile C1", "QObject", "void* arg1, QObject* parent"),
        "_ZN17QWebEngineProfileC2ERK7QStringP7QObject": ("QWebEngineProfile C2", "QObject", "void* arg1, QObject* parent"),
        "_ZN14QWebEnginePageC1EP17QWebEngineProfileP7QObject": ("QWebEnginePage C1", "QObject", "void* arg1, QObject* parent"),
        "_ZN14QWebEnginePageC2EP17QWebEngineProfileP7QObject": ("QWebEnginePage C2", "QObject", "void* arg1, QObject* parent"),
        "_ZN14QWebEnginePageC1EP7QObject": ("QWebEnginePage C1", "QObject", "QObject* parent"),
        "_ZN14QWebEnginePageC2EP7QObject": ("QWebEnginePage C2", "QObject", "QObject* parent"),
    }

    manual_destructors = {
        "_ZN14QWebEngineViewD0Ev": ("QWebEngineView D0", "QWidget"),
        "_ZN14QWebEngineViewD1Ev": ("QWebEngineView D1", "QWidget"),
        "_ZN14QWebEngineViewD2Ev": ("QWebEngineView D2", "QWidget"),
        "_ZN17QWebEngineProfileD0Ev": ("QWebEngineProfile D0", "QObject"),
        "_ZN17QWebEngineProfileD1Ev": ("QWebEngineProfile D1", "QObject"),
        "_ZN17QWebEngineProfileD2Ev": ("QWebEngineProfile D2", "QObject"),
        "_ZN14QWebEnginePageD0Ev": ("QWebEnginePage D0", "QObject"),
        "_ZN14QWebEnginePageD1Ev": ("QWebEnginePage D1", "QObject"),
        "_ZN14QWebEnginePageD2Ev": ("QWebEnginePage D2", "QObject"),
    }

    custom_returns = {
        "_ZNK14QWebEngineView10pageActionEN14QWebEnginePage9WebActionE": ("void*", "new QAction(nullptr)"),
        "_ZNK14QWebEngineView8sizeHintEv": ("QSize", "QSize(0, 0)")
    }

    stateful_skips = [
        "_ZNK14QWebEngineView4pageEv",
        "_ZN14QWebEngineView7setPageEP14QWebEnginePage",
        "_ZN14QWebEnginePage11qt_metacastEPKc",
        "_ZN14QWebEnginePage11qt_metacallEN11QMetaObject4CallEiPPv",
        "_ZN14QWebEngineView11qt_metacastEPKc",
        "_ZN14QWebEngineView11qt_metacallEN11QMetaObject4CallEiPPv",
    ]

    meta_objects = []

    with open("./packages/qtwebengine-stub/stub.cpp", "w") as f:
        f.write("#include <stdio.h>\n")
        f.write("#include <stdlib.h>\n")
        f.write("#include <string.h>\n")
        f.write("#include <new>\n")
        f.write("#include <unordered_map>\n")
        f.write("#include <QtWidgets/QWidget>\n")
        f.write("#include <QtWidgets/QAction>\n")
        f.write("#include <QtCore/QObject>\n")
        f.write("#include <QtCore/QSize>\n\n")
        f.write("extern \"C\" {\n")
        f.write("    static char dummy_object[2048] = {0};\n")
        
        f.write("    static std::unordered_map<void*, void*> view_pages;\n\n")

        f.write("    // --- Placement New Constructors ---\n")
        for sym, (log_name, base_class, args) in manual_overrides.items():
            f.write(f"    void {sym}(void* this_ptr, {args}) {{\n")
            f.write(f"        printf(\"[Stub] {log_name} (Placement new {base_class})\\n\"); fflush(stdout);\n")
            f.write(f"        new (this_ptr) {base_class}(parent);\n")
            f.write(f"    }}\n\n")

        f.write("    // --- Manual Destructors ---\n")
        for sym, (log_name, base_class) in manual_destructors.items():
            f.write(f"    void {sym}(void* this_ptr) {{\n")
            f.write(f"        printf(\"[Stub] {log_name} (Detaching {base_class} from Qt)\\n\"); fflush(stdout);\n")
            
            if "QWebEngineView" in log_name:
                f.write(f"        view_pages.erase(this_ptr);\n")
            if "QWebEnginePage" in log_name:
                f.write(f"        for (auto& pair : view_pages) {{\n")
                f.write(f"            if (pair.second == this_ptr) pair.second = nullptr;\n")
                f.write(f"        }}\n")
            f.write(f"        reinterpret_cast<{base_class}*>(this_ptr)->{base_class}::~{base_class}();\n")
            f.write(f"    }}\n\n")


        f.write("    // --- Stateful Overrides ---\n")
        f.write("    void _ZN14QWebEngineView7setPageEP14QWebEnginePage(void* this_ptr, void* page_ptr) {\n")
        f.write("        printf(\"[Stub] QWebEngineView::setPage() -> Mapping page to view\\n\"); fflush(stdout);\n")
        f.write("        view_pages[this_ptr] = page_ptr;\n")
        f.write("    }\n\n")
        
        f.write("    void* _ZNK14QWebEngineView4pageEv(void* this_ptr) {\n")
        f.write("        printf(\"[Stub] QWebEngineView::page() -> Fetching mapped page\\n\"); fflush(stdout);\n")
        f.write("        return view_pages[this_ptr];\n")
        f.write("    }\n\n")

        f.write("    void* _ZN14QWebEnginePage11qt_metacastEPKc(void* this_ptr, const char* name) {\n")
        f.write("        printf(\"[Stub] QWebEnginePage::qt_metacast(%s)\\n\", name ? name : \"NULL\"); fflush(stdout);\n")
        f.write("        if (name && strcmp(name, \"QWebEnginePage\") == 0) return this_ptr;\n")
        f.write("        return reinterpret_cast<QObject*>(this_ptr)->qt_metacast(name);\n")
        f.write("    }\n\n")

        f.write("    int _ZN14QWebEnginePage11qt_metacallEN11QMetaObject4CallEiPPv(void* this_ptr, QMetaObject::Call call, int id, void** arguments) {\n")
        f.write("        printf(\"[Stub] QWebEnginePage::qt_metacall(%d, %d)\\n\", (int)call, id); fflush(stdout);\n")
        f.write("        return reinterpret_cast<QObject*>(this_ptr)->qt_metacall(call, id, arguments);\n")
        f.write("    }\n\n")

        f.write("    void* _ZN14QWebEngineView11qt_metacastEPKc(void* this_ptr, const char* name) {\n")
        f.write("        printf(\"[Stub] QWebEngineView::qt_metacast(%s)\\n\", name ? name : \"NULL\"); fflush(stdout);\n")
        f.write("        if (name && strcmp(name, \"QWebEngineView\") == 0) return this_ptr;\n")
        f.write("        return reinterpret_cast<QWidget*>(this_ptr)->qt_metacast(name);\n")
        f.write("    }\n\n")

        f.write("    int _ZN14QWebEngineView11qt_metacallEN11QMetaObject4CallEiPPv(void* this_ptr, QMetaObject::Call call, int id, void** arguments) {\n")
        f.write("        printf(\"[Stub] QWebEngineView::qt_metacall(%d, %d)\\n\", (int)call, id); fflush(stdout);\n")
        f.write("        return reinterpret_cast<QWidget*>(this_ptr)->qt_metacall(call, id, arguments);\n")
        f.write("    }\n\n")

        f.write("    // --- Auto-Generated Stubs ---\n")
        for line in result.stdout.splitlines():
            if "UND" in line and "WebEngine" in line:
                parts = line.split()
                if len(parts) < 8: continue
                
                sym_type = parts[3]
                sym_name = parts[7].split('@')[0]

                if sym_name in manual_overrides or sym_name in manual_destructors or sym_name in stateful_skips: 
                    continue

                if sym_type == "FUNC":
                    if sym_name in custom_returns:
                        ret_type, ret_val = custom_returns[sym_name]
                        f.write(f"    {ret_type} {sym_name}() {{\n")
                        f.write(f"        printf(\"[Stub] Called: {sym_name}\\n\"); fflush(stdout);\n")
                        f.write(f"        return {ret_val};\n")
                        f.write(f"    }}\n")
                    else:
                        f.write(f"    void* {sym_name}() {{\n")
                        f.write(f"        printf(\"[Stub] Called: {sym_name}\\n\"); fflush(stdout);\n")
                        f.write(f"        return &dummy_object;\n")
                        f.write(f"    }}\n")
                        
                elif sym_type == "OBJECT":
                    if "staticMetaObject" in sym_name:
                        f.write(f"    QMetaObject {sym_name};\n")
                        meta_objects.append(sym_name)
                    else:
                        f.write(f"    void* {sym_name}[32] = {{0}};\n")
        
        f.write("\n    // Copy a real QMetaObject into our dummy meta objects on library load\n")
        f.write("    __attribute__((constructor)) void init_meta_objects() {\n")
        for mo in meta_objects:
            if "QWebEngineView" in mo:
                f.write(f"        memcpy(&{mo}, &QWidget::staticMetaObject, sizeof(QMetaObject));\n")
                f.write(f"        *(const QMetaObject**)&{mo} = &QWidget::staticMetaObject;\n")
            elif "QWebEnginePage" in mo:
                f.write(f"        memcpy(&{mo}, &QObject::staticMetaObject, sizeof(QMetaObject));\n")
                f.write(f"        *(const QMetaObject**)&{mo} = &QObject::staticMetaObject;\n")
            else:
                f.write(f"        memcpy(&{mo}, &QObject::staticMetaObject, sizeof(QMetaObject));\n")
        f.write("    }\n")

        f.write("}\n")
    print("Generated stub.cpp!")

if __name__ == "__main__":
    generate()
