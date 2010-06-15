from    AppKit      import *
from    Foundation  import *
from    QFAlert     import *
from    QFApp       import QFApp
import  objc

class QuoteFixPreferencesController(NSObject):
    removeQuotes                = objc.IBOutlet()
    removeQuotesLevel           = objc.IBOutlet()
    keepAttributionWhitespace   = objc.IBOutlet()
    debugging                   = objc.IBOutlet()
    _window                     = objc.IBOutlet()

    def set_remove_quotes_level(self):
        value = self.removeQuotesLevel.intValue()
        if value < 1:
            QFAlert.showAlert(self, "Invalid level", "Please enter a level of 1 or higher.")
            return
        self.removeQuotes.setState_(1)
        QFApp().remove_quotes = True
        QFApp().remove_quotes_level = value

    @objc.IBAction
    def changeRemoveQuotes_(self, sender):
        if sender.state():  # enable
            self.set_remove_quotes_level()
        else:               # disable
            QFApp().remove_quotes = False

    @objc.IBAction
    def changeRemoveQuotesLevel_(self, sender):
        self.set_remove_quotes_level()

    @objc.IBAction
    def changeDebugging_(self, sender):
        QFApp().debugging = sender.state()

    @objc.IBAction
    def changeKeepAttributionWhitespace_(self, sender):
        QFApp().attribution_whitespace = sender.state()

    def awakeFromNib(self):
        app = QFApp()
        self.keepAttributionWhitespace.setState_(app.attribution_whitespace)
        self.debugging.setState_(app.debugging)
        self.removeQuotes.setState_(app.remove_quotes)
        self.removeQuotesLevel.setIntValue_(app.remove_quotes_level)

    def window(self):
        """ Called by QFAlert() """
        return self._window
