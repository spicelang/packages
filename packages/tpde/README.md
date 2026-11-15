# tpde

Spice bindings for [TPDE](https://github.com/tpde2/tpde), a compiler back end framework, that compiles LLVM modules to
ELF objects with `-O0`-like code quality, but a lot faster than the LLVM back end. These are the bindings behind the
experimental TPDE backend of the Spice compiler (`spice build --backend=tpde`).

TPDE emits ELF objects for **x86_64 and aarch64 Linux** only. On other platforms, and if the TPDE libraries are not linked,
the bindings still compile and link, but `isAvailable()` returns false and no compiler is valid.

## Installation

```toml
[dependencies]
tpde = "^0.1.0"
```

```spice
import "spice_packages/llvm/llvm" as llvm;
import "spice_packages/tpde/tpde" as tpde;
```

The package builds on the [llvm](https://rack.spicelang.com/packages/llvm) package, which Spice Shaker installs along
with it. Its LLVM requirements apply (a static LLVM 23 build, found via `LLVM_LIB_DIR` and `LLVM_INCLUDE_DIRS`, see the llvm package README). The package
imports the llvm package from the `spice_packages` dir next to the main source file, so the main source file has to be in
the project root, where Spice Shaker puts `spice_packages`.

The TPDE headers and static libraries are read from the `TPDE_FLAGS` environment variable on Linux:

| Setup                                       | `TPDE_FLAGS`                                                                              |
|---------------------------------------------|-------------------------------------------------------------------------------------------|
| Spice Linux release package                 | Nothing to do: the release ships TPDE in its std and the compiler sets `TPDE_FLAGS` itself |
| Own TPDE build (e.g. a Spice source checkout) | `-I<include dir> -Wl,--start-group <dir>/libtpde_llvm.a <dir>/libtpde.a <dir>/libfadec.a <dir>/libdisarm64.a <dir>/libspdlog.a -Wl,--end-group` |

TPDE has to be built against the same LLVM major version as the llvm package. In a Spice source checkout,
`python setup-deps.py --tpde` builds it into `std/bindings/tpde/lib` and `std/bindings/tpde/include`, which the compiler
then picks up like the ones of a release.

## Quick start

```spice
import "std/data/vector";
import "spice_packages/llvm/llvm" as llvm;
import "spice_packages/tpde/tpde" as tpde;

f<int> main() {
    if !tpde::isAvailable() {
        printf("TPDE is not available on this platform\n");
        return 1;
    }

    llvm::initializeNativeTarget();
    llvm::initializeNativeAsmPrinter();
    const llvm::Triple triple = llvm::getDefaultTargetTriple();
    string error;
    llvm::Target target = llvm::getTargetFromTriple(triple, &error);
    llvm::TargetMachine targetMachine = target.createTargetMachine(triple, "generic", "", llvm::LLVMCodeGenOptLevel::None,
        llvm::LLVMRelocMode::PIC, llvm::LLVMCodeModel::Default);

    // int add(int a, int b) { return a + b; }
    llvm::LLVMContext context;
    llvm::Module module = llvm::Module("add", context);
    module.setDataLayout(targetMachine.createDataLayout());
    module.setTargetTriple(triple);
    llvm::IRBuilder builder = llvm::IRBuilder(context);
    Vector<llvm::Type> argTypes;
    argTypes.pushBack(builder.getInt32Ty());
    argTypes.pushBack(builder.getInt32Ty());
    llvm::Function addFct = llvm::Function(module, "add", llvm::getFunctionType(builder.getInt32Ty(), argTypes));
    llvm::BasicBlock entry = llvm::BasicBlock(context, "");
    addFct.pushBack(entry);
    builder.setInsertPoint(entry);
    builder.createRet(builder.createAdd(addFct.getArg(0u), addFct.getArg(1u), "sum"));

    // Compile the module with TPDE instead of the LLVM back end
    tpde::Compiler compiler = tpde::Compiler(triple);
    String errorMessage;
    if compiler.compileToFile(module, "add.o", errorMessage) {
        printf("Compilation failed: %s\n", errorMessage.getRaw());
        return 1;
    }
    printf("Wrote add.o\n");
}
```

## API

| Type / function    | Members                                                                                                  |
|--------------------|----------------------------------------------------------------------------------------------------------|
| `isAvailable`      | Whether the bindings are backed by TPDE (Linux and the TPDE libraries linked)                            |
| `Compiler`         | `Compiler(triple)`, `isValid`, `compileToFile(module, filename, errorMessage)`, `compileToBuffer(module, bytes, errorMessage)` |

A `Compiler` is only valid if TPDE supports its target triple (x86_64 and aarch64 ELF). The compile methods return true
if the compilation failed and put the reason into the error message; on success they clear it. TPDE may modify the
module during compilation. Copies of a compiler create their own TPDE compiler for the same target.
