# libcurl

Spice bindings for [libcurl](https://curl.se/libcurl), used for network transfers that need https.

## Installation

```toml
[dependencies]
libcurl = "^0.1.0"
```

```spice
import "spice_packages/libcurl/libcurl";
```

The package links against the system libcurl, so its development files have to be installed:

| Platform      | Package                |
|---------------|------------------------|
| Debian/Ubuntu | `libcurl4-openssl-dev` |
| Fedora        | `libcurl-devel`        |
| macOS         | `brew install curl`    |
| Windows       | `vcpkg install curl:x64-windows` (add its `lib` dir to `LIBRARY_PATH`) |

## Quick start

```spice
import "spice_packages/libcurl/libcurl";

f<int> main() {
    CurlClient client;
    Result<string> res = client.downloadFile("https://example.com/index.html", "./index.html");
    if res.isErr() {
        const Error& err = res.getErr();
        printf("Download failed: %s\n", err.getMessage());
        return 1;
    }
    printf("Saved to %s\n", res.unwrap());
}
```

## API

| Type         | Members                                                                                             |
|--------------|-----------------------------------------------------------------------------------------------------|
| `CurlClient` | `CurlClient(globalInitFlags)`, `downloadFile(url, outputPath, withProgress)`                        |

`downloadFile` follows redirects and overwrites the output file. Pass `true` as `withProgress` to let libcurl print a
progress meter. The `CURL_GLOBAL_*` constants select what `curl_global_init` initializes and default to
`CURL_GLOBAL_DEFAULT`.

For plain HTTP and HTTPS requests without an external library, see `std/net/http-client` of the standard library.
