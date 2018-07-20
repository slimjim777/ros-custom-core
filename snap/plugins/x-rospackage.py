import snapcraft
import subprocess
import shlex
import os

PREREQ = ['coreutils', 'dctrl-tools', 'sed', 'wget']

class XRospackagePlugin(snapcraft.BasePlugin):

    @classmethod
    def schema(cls):
        schema = super().schema()

        schema['properties']['release'] = {
            'type': 'string',
            'default': '',
        }
        schema['properties']['rosdistro'] = {
            'type': 'string',
            'default': '',
        }
        schema['properties']['rospackages'] = {
            'type': 'array',
            'minitems': 1,
            'uniqueItems': True,
            'items': {
                'type': 'string'
            },
            'default': [],
        }

        schema['build-properties'].extend(['release'])
        schema['build-properties'].extend(['rosdistro'])
        schema['build-properties'].extend(['rospackages'])

        return schema

    def __init__(self, name, options, project):
        super().__init__(name, options, project)
        for p in PREREQ:
            self.build_packages.append(p)

    def build(self):
        super().build()
        packages = 'http://packages.ros.org/ros/ubuntu/dists/%s/main/binary-armhf/Packages.gz' % self.options.release

        for pkg in self.options.rospackages:
            # Get the path to the deb package
            cmd = "wget -q -O- %s | zcat | grep-dctrl %s |\
                    grep %s/ | grep Filename | tail -1 | sed 's/^Filename: //'" % (packages, pkg, pkg)
            pipes = cmd.split("|")

            procs = []
            prev_ps = None
            for p in pipes:
                args = shlex.split(p)
                if prev_ps is None:
                    ps = subprocess.Popen(args, stdout=subprocess.PIPE)
                else:
                    ps = subprocess.Popen(
                            args,
                            stdin=prev_ps.stdout,
                            stdout=subprocess.PIPE)

                procs.append(ps)
                prev_ps = ps

            last_process = procs[-1]
            output, _ = last_process.communicate()
            pkg_path = output[:-1].decode('utf-8')
            pkg_file = os.path.basename(pkg_path)

            # Download the deb package and extract the files
            self.run(['wget', 'http://packages.ros.org/ros/ubuntu/%s' % pkg_path])
            self.run(['dpkg', '-x', pkg_file, 'unpack/'])
            self.run(['sh', '-c', 'cp -aR unpack/* $SNAPCRAFT_PART_INSTALL/'])

