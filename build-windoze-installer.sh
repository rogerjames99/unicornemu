# Extracts all dependencies and places them in the pynsist_pkgs folder

rm -r pynsist_pkgs

mkdir pynsist_pkgs

# Unzip the bindings
7z x pygi.exe -opygi

# Copy the PyGI packages into the pynsist_pkgs folder
# Change this line for the correct bitness and python version
7z x pygi/binding/py2.7-64/py2.7-64.7z -obindings
cp -r bindings/* pynsist_pkgs
rm -r bindings

# Copy the noarch and specified architecture dependencies into the gnome folder
array=( ATK Base GDK GDKPixbuf GTK JPEG Pango WebP TIFF HarfBuzz)

for i in "${array[@]}"
do
    echo -e "\nProcessing $i dependency"
    7z x pygi/noarch/$i/$i.data.7z -o$i-noarch
    cp -r $i-noarch/gnome/* pynsist_pkgs/gnome
    rm -r $i-noarch

    7z x pygi/rtvc9-64/$i/$i.bin.7z -o$i-arch
    cp -r $i-arch/gnome/* pynsist_pkgs/gnome
    rm -r $i-arch
done

#Remove pygi Folder
rm -r pygi

#Compile glib schemas
glib-compile-schemas pynsist_pkgs/gnome/share/glib-2.0/schemas/

# Use pynsist to build the nsis installer
pynsist unicornemu-installer.cfg
