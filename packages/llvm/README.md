# llvm

Spice bindings for the [LLVM](https://llvm.org) C API, to build LLVM IR, optimize it with the new pass manager and emit
object files or assembly. These are the bindings that the Spice compiler itself is built with.

## Installation

```toml
[dependencies]
llvm = "^0.1.0"
```

```spice
import "spice_packages/llvm/llvm" as llvm;
```

Importing the package with an alias (`as llvm`) is recommended, because its type names (`Module`, `Function`, `Type`,
`Value`, ...) are very generic.

The package links LLVM **statically** and targets **LLVM 23** (the version the Spice compiler is built against). It
initializes and links the AArch64, WebAssembly and X86 targets. The location of the LLVM libraries and headers is read
from two environment variables at build time:

| Variable            | Content                                                    | Example                                                       |
|---------------------|------------------------------------------------------------|---------------------------------------------------------------|
| `LLVM_LIB_DIR`      | Directory with the static LLVM libraries (`libLLVM*.a`)    | `/opt/llvm/build/lib`                                          |
| `LLVM_INCLUDE_DIRS` | One or more `-I<dir>` flags with the LLVM headers          | `-I/opt/llvm/llvm/include -I/opt/llvm/build/include`           |

For an installed LLVM, `export LLVM_LIB_DIR="$(llvm-config --libdir)" LLVM_INCLUDE_DIRS="-I$(llvm-config --includedir)"`
sets both. Besides LLVM, these system libraries are linked:

| Platform      | Packages                                                                          |
|---------------|-----------------------------------------------------------------------------------|
| Debian/Ubuntu | `zlib1g-dev libzstd-dev libtinfo-dev uuid-dev`                                    |
| Fedora        | `zlib-devel libzstd-devel ncurses-devel libuuid-devel`                            |
| macOS         | `brew install zlib zstd ncurses` (Homebrew's `lib` dir is added to the search path) |
| Windows       | MinGW-w64 (`ole32`, `ws2_32`, `ntdll` and `uuid` come with it)                    |

LLVM itself can be built like the Spice CI does it:

```sh
git clone --depth 1 --branch llvmorg-23.1.5 https://github.com/llvm/llvm-project llvm
cmake -S llvm/llvm -B llvm/build -GNinja -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="AArch64;X86;WebAssembly" \
  -DLLVM_BUILD_TOOLS=OFF -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_INCLUDE_BENCHMARKS=OFF
cmake --build llvm/build
export LLVM_LIB_DIR="$PWD/llvm/build/lib" LLVM_INCLUDE_DIRS="-I$PWD/llvm/llvm/include -I$PWD/llvm/build/include"
```

## Quick start

```spice
import "std/data/vector";
import "spice_packages/llvm/llvm" as llvm;

f<int> main() {
    llvm::initializeNativeTarget();
    llvm::initializeNativeAsmPrinter();

    // Target machine for the host
    const llvm::Triple triple = llvm::getDefaultTargetTriple();
    string error;
    llvm::Target target = llvm::getTargetFromTriple(triple, &error);
    llvm::TargetMachine targetMachine = target.createTargetMachine(triple, "generic", "", llvm::LLVMCodeGenOptLevel::Default,
        llvm::LLVMRelocMode::PIC, llvm::LLVMCodeModel::Default);

    // int main() { printf("Hello, world!\n"); return 0; }
    llvm::LLVMContext context;
    llvm::Module module = llvm::Module("hello", context);
    module.setDataLayout(targetMachine.createDataLayout());
    module.setTargetTriple(triple);
    llvm::IRBuilder builder = llvm::IRBuilder(context);

    Vector<llvm::Type> argTypes;
    llvm::Function mainFct = llvm::Function(module, "main", llvm::getFunctionType(builder.getInt32Ty(), argTypes));
    llvm::BasicBlock entry = llvm::BasicBlock(context, "");
    mainFct.pushBack(entry);
    builder.setInsertPoint(entry);

    Vector<llvm::Type> printfArgTypes;
    printfArgTypes.pushBack(builder.getPtrTy());
    llvm::Function printfFct = module.getOrInsertFunction("printf", llvm::getFunctionType(builder.getInt32Ty(), printfArgTypes, true));
    Vector<llvm::Value> printfArgs;
    printfArgs.pushBack(builder.createGlobalString("Hello, world!\n", "str"));
    builder.createCall(printfFct, printfArgs);
    builder.createRet(builder.getInt32(0));

    llvm::Message verifierOutput;
    assert !llvm::verifyModule(module, verifierOutput);

    // Optimize with the O2 pipeline and emit an object file, which can be linked with e.g. `cc hello.o -o hello`
    llvm::PassBuilderOptions options;
    llvm::PassBuilder passBuilder = llvm::PassBuilder(options);
    passBuilder.buildPerModuleDefaultPipeline(llvm::OptimizationLevel::O2);
    passBuilder.run(module, targetMachine);

    const llvm::Message ir = module.print();
    printf("%s", ir.get());
    targetMachine.emitToFile(module, "hello.o", llvm::LLVMCodeGenFileType::ObjectFile);
}
```

## API

The package wraps the LLVM C API in Spice types. Each wrapper owns its LLVM object and disposes it in its destructor
where LLVM requires that (context, module, builder, target machine, messages, ...).

| Type / function                                  | Purpose                                                                                     |
|--------------------------------------------------|---------------------------------------------------------------------------------------------|
| `LLVMContext`, `DiagnosticCollector`             | LLVM context, optionally collecting the diagnostics LLVM reports                            |
| `Module`, `Comdat`                               | Modules (functions, globals, data layout, target triple, flags, printing, linking)          |
| `Type`, `StructType`, `get*Ty`, `getFunctionType` | Types                                                                                       |
| `Value`, `Constant`, `getConst*`, `getNullValue` | Values and constants                                                                        |
| `Function`, `BasicBlock`                         | Functions (attributes, linkage, calling convention, ...) and their basic blocks              |
| `IRBuilder`                                      | Instruction builder (`createAdd`, `createCall`, `createLoad`, `createStore`, `createBr`, ...) |
| `Metadata`, `DIBuilder`                          | Metadata and debug info                                                                     |
| `Triple`, `Target`, `TargetMachine`, `DataLayout` | Target selection, code generation (`emitToFile`, `emitToString`) and type layout            |
| `PassBuilderOptions`, `PassBuilder`              | New pass manager pipelines (`buildPerModuleDefaultPipeline`, `run`)                         |
| `verifyFunction`, `verifyModule`                 | IR verifier                                                                                 |
| `initializeNative*`, `initializeAll*`            | Target initialization                                                                       |
| `getVersion`, `getVersionString`                 | Version of the linked LLVM                                                                  |
| `Message`, `LLVMError`                           | Owned LLVM messages and errors                                                              |

The LLVM C enums are available as `LLVMOpcode`, `LLVMTypeKind`, `LLVMLinkage`, `LLVMCallConv`, `LLVMIntPredicate`,
`LLVMCodeGenOptLevel`, `LLVMRelocMode`, `LLVMCodeModel`, `LLVMCodeGenFileType`, `OptimizationLevel` and friends.
