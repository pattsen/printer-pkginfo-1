printer-pkginfo
===============

Creates a nopkg-style pkginfo file from a plist file to install printers with
[Munki](https://github.com/munki/munki).

### Usage

After cloning the repo to your local system (this doesn't have to be the same
system that you're running Munki on, but if it's not, that adds an extra step),
copy the `example-printer.plist` file and edit the options to fit your own
printer setup.

Note that the `requires` string must match the name of the driver package
installed on the target systems. If the drivers are unavailable from your
Munki server and aren't found on the target system, the install will fail.

After you've edited the plist file for your printer, run `printer-pkginfo`

```
./printer-pkginfo --plist example-printer.plist > example_pkginfo-1.0.plist
```

Move the resulting plist file to your `pkgsinfo/` directory on your Munki
server, then rebuild the catalogs using `makecatalogs`. You can now add the
printer to manifests using `manifestutil`, where the `name` key from your
originating plist file corresponds to the package name in Munki.
