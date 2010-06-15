from    AppKit      import *
from    Foundation  import *
from    QFMenu      import *
from    QFAlert     import *
import  objc, os.path

class QFApp(object):

    __shared_state = {}

    def __init__(self, version = None):
        # use Borg pattern
        self.__dict__ = self.__shared_state

        # already configured?
        if 'version' in self.__dict__:
            return

        # set version
        self.version = version

        # store main window
        self.mainwindow = NSApplication.sharedApplication().mainWindow()

        # read user defaults
        self.userdefaults = NSUserDefaults.standardUserDefaults()

        # check if we're running in a different Mail version as before
        infodict    = NSBundle.mainBundle().infoDictionary()
        mailversion = infodict['CFBundleVersion']
        lastknown   = self.get_pref("QuoteFixLastKnownBundleVersion", 'string')
        if lastknown and mailversion != lastknown:
            QFAlert.showAlert(self,
                'QuoteFix plug-in',
                '''
The QuoteFix plug-in detected a different Mail.app version (perhaps you updated?).

If you run into any problems with regards to replying or forwarding mail, consider removing this plug-in (from ~/Library/Mail/Bundles/).

(This alert is only displayed once for each new version of Mail.app)
''', alert_style = NSInformationalAlertStyle)

        self.set_pref("QuoteFixLastKnownBundleVersion", mailversion)

        # check if quotefixing should be turned on
        self.is_active = self.get_pref("QuoteFixDisabled", 'bool') and False or True

        # check if debugging should be turned on
        self.is_debugging = self.get_pref("QuoteFixEnableDebugging", 'bool') and True or False

        # check if 'keep whitespace after attribution' is turned on
        self.keep_attribution_whitespace = self.get_pref("QuoteFixKeepAttributionWhitespace", 'bool') and True or False

        # check for remove-quotes
        self.remove_quotes          = self.get_pref("QuoteFixRemoveQuotes", 'bool') and True or False
        self.remove_quotes_level    = self.get_pref("QuoteFixRemoveQuotesLevel", 'int') or 5

        # inject menu
        self.menu = QFMenu.alloc().initWithApp_(self)
        self.menu.inject()

        # demand-load preferences
        self.preferences_loaded = False

    # get/set preferences
    def get_pref(self, name, type = 'object'):
        method = {
            'string'    : self.userdefaults.stringForKey_,
            'bool'      : self.userdefaults.boolForKey_,
            'object'    : self.userdefaults.objectForKey_,
            'int'       : self.userdefaults.integerForKey_,
        }.get(type)
        return method(name)

    def set_pref(self, name, value, type = 'object'):
        method = {
            'object'    : self.userdefaults.setObject_forKey_,
            'bool'      : self.userdefaults.setBool_forKey_,
            'int'       : self.userdefaults.setInteger_forKey_,
        }.get(type)
        method(value, name)

    # get/set 'is plugin active?'
    def get_isactive(self):
        return self.is_active

    def set_isactive(self, active):
        # store in preferences
        self.set_pref("QuoteFixDisabled", not active, 'bool')
        self.is_active = active

    active = property(get_isactive, set_isactive)

    # get/set debugging
    def get_debugging(self):
        return self.is_debugging

    def set_debugging(self, debugging):
        # store in preferences
        self.set_pref("QuoteFixEnableDebugging", debugging, 'bool')
        self.is_debugging = debugging

    debugging = property(get_debugging, set_debugging)

    # get/set 'keep whitespace after attribution'
    def get_keep_attribution_whitespace(self):
        return self.keep_attribution_whitespace

    def set_keep_attribution_whitespace(self, keep):
        # store in preferences
        self.set_pref("QuoteFixKeepAttributionWhitespace", keep)
        self.keep_attribution_whitespace = keep

    attribution_whitespace = property(get_keep_attribution_whitespace, set_keep_attribution_whitespace)

    # get/set 'remove quotes from level'
    def get_remove_quotes_level(self):
        return self.remove_quotes_level_value

    def set_remove_quotes_level(self, level):
        # store in preferences
        self.set_pref("QuoteFixRemoveQuotesLevel", level, 'int')
        self.remove_quotes_level_value = level

    remove_quotes_level = property(get_remove_quotes_level, set_remove_quotes_level)

    # get/set 'remove quotes from level
    def get_remove_quotes(self):
        return self.remove_quotes_value

    def set_remove_quotes(self, remove):
        # store in preferences
        self.set_pref("QuoteFixRemoveQuotes", remove, 'bool')
        self.remove_quotes_value = remove

    remove_quotes = property(get_remove_quotes, set_remove_quotes)

    # used for debugging
    def set_html(self, html):
        if self.menu:
            self.menu.set_html(html)
    html = property(None, set_html)

    # return reference to main window
    def window(self):
        return self.mainwindow

    # show preferences window
    def showPreferencesWindow(self):
        # load preferences NIB for the first time
        if not self.preferences_loaded:
            resourcepath    = NSBundle.bundleWithIdentifier_('name.klep.mail.QuoteFix').resourcePath()
            nibfile         = os.path.join(resourcepath, "QuoteFixPreferences.nib")
            context         = { NSNibTopLevelObjects : [] }
            NSBundle.loadNibFile_externalNameTable_withZone_(nibfile, context, None)
            self.preferencesWindow  = filter(lambda _: isinstance(_, NSWindow), context[NSNibTopLevelObjects])[0]
            self.preferences_loaded = True
        # show preferences window
        if self.preferencesWindow:
            self.preferencesWindow.makeKeyAndOrderFront_(self)
