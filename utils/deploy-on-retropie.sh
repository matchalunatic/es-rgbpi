#!/bin/bash
if [ "$1" != "force" ]; then
echo "This will install es-rgbpi on your Retropie installation."
echo "Press Enter to continue or ^C to cancel"

read _

fi

test ! -e /home/pi/RGBPI_PARAMS && cat > /home/pi/RGBPI_PARAMS <<EOF
#!/bin/sh
export RGBPI_X_OFFSET="0"
export RGBPI_Y_OFFSET="3"
export RGBPI_H_SIZE="-288"
export RGBPI_H_ZOOM="-40"
export DISPLAY_FREQUENCY='NTSC'
export TRINITRON_FIX=0
EOF

echo "Downloading es-rgbpi master"
wget -O /tmp/es-rgbpi.tgz https://github.com/ChloeTigre/es-rgbpi/archive/master.tar.gz
echo "Extracting"
cd /tmp
tar xvf es-rgbpi.tgz
cd es-rgbpi-master/install
echo "Deploying es-rgbpi components to /opt/retropie (not overwriting already existing files)"
cp -nrv opt/retropie/* /opt/retropie/
cd ..
echo "Installing resolution management system in /opt/retropie/extras"
mkdir /opt/retropie/extras/
cp -nrv *.py rgbpi/ data/ /opt/retropie/extras
fgrep runcommand_retroarch_append_config.sh /opt/retropie/supplementary/runcommand/runcommand.sh || for _ in 1; do
    cat > /tmp/runcommand.patch <<'EOF'
--- /tmp/runcommand.sh.a	2019-08-15 00:53:47.229302093 +0200
+++ /tmp/runcommand.sh.b	2019-08-15 00:53:51.949219789 +0200
@@ -1057,6 +1057,7 @@
     [[ -n "$GOVERNOR" ]] && set_governor "$GOVERNOR"
 
     retroarch_append_config
+    user_script "runcommand-retroarch_append_config.sh"
 
     # workaround for launching xserver on correct/user owned tty
     # see https://github.com/RetroPie/RetroPie-Setup/issues/1805

EOF
    sudo patch -p0 /opt/retropie/supplementary/runcommand/runcommand.sh /tmp/runcommand.patch
    rm /tmp/runcommand.patch
done
