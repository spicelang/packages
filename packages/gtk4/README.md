# gtk4

Spice bindings for the [GTK 4](https://gtk.org) GUI toolkit.

## Installation

```toml
[dependencies]
gtk4 = "^0.1.0"
```

```spice
import "spice_packages/gtk4/gtk4";
```

The package links against the system GTK 4 library, so its development files have to be installed:

| Platform      | Package            |
|---------------|--------------------|
| Debian/Ubuntu | `libgtk-4-dev`     |
| Fedora        | `gtk4-devel`       |
| macOS         | `brew install gtk4` |
| Windows       | GTK 4 from [MSYS2](https://www.gtk.org/docs/installations/windows) (add its `lib` dir to `LIBRARY_PATH`) |

## Quick start

Build the widget tree in code:

```spice
import "spice_packages/gtk4/gtk4";

p onYesClick(GtkWidget widget) {
    gPrint("Hello World!\n");
}

p onCancelClick(GtkWidget widget, GtkWindow window) {
    window.destroy();
}

p activate(GtkApplication app, GPointer data) {
    dyn window = app.newWindow();
    window.setTitle("Do you want to continue");
    window.setDefaultSize(350, 140);

    dyn box = GtkBox(GtkOrientation::Horizontal);
    box.setHAlign(GtkAlign::Center);
    box.setVAlign(GtkAlign::Center);
    window.setChild(box);

    dyn btnCancel = GtkButton("Cancel");
    btnCancel.setOnClickCallback(onCancelClick, window);
    box.append(btnCancel);

    dyn btnYes = GtkButton("Yes");
    btnYes.setOnClickCallback(onYesClick);
    box.append(btnYes);

    window.present();
}

f<int> main(int argc, string[] argv) {
    dyn app = GtkApplication("com.example.App");
    app.setActivateCallback(activate);
    return app.run(argc, argv);
}
```

Or load it from a [GtkBuilder UI file](https://docs.gtk.org/gtk4/class.Builder.html):

```spice
p activate(GtkApplication app, GPointer data) {
    GtkBuilder builder;
    Result<bool> result = builder.addFromFile("window.ui");
    if result.isErr() {
        const Error& err = result.getErr();
        err.triggerPanic();
    }
    dyn window = builder.getObject<GtkWindow>("window");
    window.setApplication(app);

    dyn button = builder.getObject<GtkButton>("button");
    button.setOnClickCallback(onYesClick);

    window.setVisible();
}
```

## API

| Type             | Members                                                                                      |
|------------------|----------------------------------------------------------------------------------------------|
| `GtkApplication` | `GtkApplication(applicationId, flags)`, `setActivateCallback`, `run`, `newWindow`            |
| `GtkWindow`      | `setTitle`, `setDefaultSize`, `setChild`, `setApplication`, `present`, `setVisible`, `close`, `destroy` |
| `GtkBox`         | `GtkBox(orientation, spacing)`, `append`, `setHAlign`, `setVAlign`                           |
| `GtkButton`      | `GtkButton(label)`, `setOnClickCallback(callback)`, `setOnClickCallback(callback, data)`    |
| `GtkWidget`      | `setHAlign`, `setVAlign`                                                                     |
| `GtkBuilder`     | `addFromFile`, `getObject<T>`                                                                |
| `gPrint`         | Print through GLib's `g_print`                                                               |

The bindings cover a small part of GTK. Contributions for more widgets are welcome.
