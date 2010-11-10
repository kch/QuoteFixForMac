from    distutils.core import setup
import  py2app, sys, os, commands

# determine version from latest revision
status, hgversion = commands.getstatusoutput("hg log -l1 -r -2 --template '{tags}'")
if status != 0:
    # probably no hg installed or not building from a repository
    hgversion = "unknown"

# define distutils setup structure
setup(
    plugin      = [ 'QuoteFix.py' ],
    version     = hgversion,
    description = "QuoteFix for Mac is a Mail.app plugin",
    data_files  = [ 'QuoteFixPreferences.nib' ],
    options     = dict(py2app = dict(
        extension   = '.mailbundle',
        includes    = [ 'QFApp', 'QFMenu', 'QFAlert', 'QFPreferences' ],
        plist       = dict(
            NSPrincipalClass                    = 'QuoteFix',
            CFBundleIdentifier                  = 'name.klep.mail.QuoteFix',
            NSHumanReadableCopyright            = '(c) 2009, Robert Klep, robert@klep.name',
            SupportedPluginCompatibilityUUIDs   = [
                # 10.6
                '225E0A48-2CDB-44A6-8D99-A9BB8AF6BA04', # Mail 4.0
                'B3F3FC72-315D-4323-BE85-7AB76090224D', # Message.framework 4.0
                # 10.6.1
                '2610F061-32C6-4C6B-B90A-7A3102F9B9C8', # Mail 4.1
                '99BB3782-6C16-4C6F-B910-25ED1C1CB38B', # Message.framework 4.1
                # 10.6.2
                '2F0CF6F9-35BA-4812-9CB2-155C0FDB9B0F', # Mail
                '0CB5F2A0-A173-4809-86E3-9317261F1745', # Message.framework
                # 10.6.4
                'B842F7D0-4D81-4DDF-A672-129CA5B32D57', # Mail 4.3
                'E71BD599-351A-42C5-9B63-EA5C47F7CE8E', # Message.framework 4.3
                # 10.6.5
                'BDD81F4D-6881-4A8D-94A7-E67410089EEB', # Mail 4.4
                '857A142A-AB81-4D99-BECC-D1B55A86D94E', # Message.framework 4.4
            ]
        )
    ))
)
