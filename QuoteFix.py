"""
QuoteFix - a Mail.app plug-in to fix some annoyances when replying to e-mail
"""

from    AppKit          import *
from    Foundation      import *
from    QFApp           import *
from    QFMenu          import *
from    QFAlert         import *
from    QFPreferences   import *
import  objc, re, random, traceback

MVMailBundle        = objc.lookUpClass('MVMailBundle')
MailDocumentEditor  = objc.lookUpClass('MailDocumentEditor')
isQuoteFixed        = {}

# remove old quotes from a message (if the user has set that preference)
def removeOldQuotes(self, root, view):
    if not QFApp().remove_quotes:
        # nothing to do
        return False

    # get level
    level = QFApp().remove_quotes_level

    # find all blockquotes
    domdocument = view.mainFrame().DOMDocument()
    blockquotes = domdocument.querySelectorAll_("blockquote")
    for i in range(blockquotes.length()):
        blockquote = blockquotes.item_(i)
        # check quotelevel against maximum allowed level
        if blockquote.quoteLevel() >= level:
            blockquote.parentNode().removeChild_(blockquote)

    return True

# try to find, and remove, signature of sender
SIGSEP = re.compile(r'--(?:&nbsp;| |\xa0)', re.M|re.S|re.I)
def removeOldSignature(self, root, view):
    signature   = None
    domdocument = view.mainFrame().DOMDocument()

    # grab first blockquote (if any)
    blockquote  = root.firstDescendantBlockQuote()
    if not blockquote:
        return False

    # find nodes which might contain senders signature
    possibles = [
        "body > div > blockquote > div >  br",
        "body > blockquote > br",
        "body > blockquote > div",
    ]

    nodes = []
    for possible in possibles:
        matches = domdocument.querySelectorAll_(possible)
        nodes += [ matches.item_(i) for i in range(matches.length()) ]

    # try to find a signature
    for node in nodes:
        # skip nodes which aren't at quotelevel 1
        if node.quoteLevel() != 1:
            continue

        # BR's are empty, so treat them differently
        if node.nodeName().lower() == 'br':
            next = node.nextSibling()
            if isinstance(next, DOMText) and SIGSEP.match(next.data()):
                signature = node
                break
        elif node.nodeName().lower() == 'div' and SIGSEP.match(node.innerHTML()):
            signature = node
            break

    # if we found a signature, remove it
    if signature:
        domrange = domdocument.createRange()
        domrange.setStartBefore_(signature)
        domrange.setEndAfter_(blockquote)
        domrange.deleteContents()

        # move down a line
        view.moveDown_(self)

        # and insert a paragraph break
        view.insertParagraphSeparator_(self)

        # remove empty lines
        blockquote.removeStrayLinefeeds()

        # signal that we removed an old signature
        return True

    # found nothing?
    return False

def moveAboveNewSignature(self, dom, view):
    # find new signature by ID
    div = dom.getElementById_("AppleMailSignature")
    if not div:
        return False

    # set selection range
    domrange = dom.createRange()
    domrange.selectNode_(div)

    # create selection
    view.setSelectedDOMRange_affinity_(domrange, 0)

    # move up (positions cursor above signature)
    view.moveUp_(self)

    # and insert a paragraph break
    view.insertParagraphSeparator_(self)

    # signal that we removed an old signature
    return True

def cleanupLayout(self, dom, root):
    # clean up stray linefeeds
    root.getElementsByTagName_("body").item_(0)._removeStrayLinefeedsAtBeginning()

    # done?
    if QFApp().attribution_whitespace:
        return True

    # clean up linebreaks before first blockquote
    blockquote = root.firstDescendantBlockQuote()
    if blockquote:
        parent  = blockquote.parentNode()
        node    = blockquote.previousSibling()
        while node and node.nodeName().lower() == 'br':
            parent.removeChild_(node)
            node = blockquote.previousSibling()

    return True

def swizzle(*args):
    cls, SEL = args
    def decorator(func):
        oldIMP      = cls.instanceMethodForSelector_(SEL)
        def wrapper(self, *args, **kwargs):
            return func(self, oldIMP, *args, **kwargs)
        newMethod   = objc.selector(wrapper, selector = oldIMP.selector, signature = oldIMP.signature)
        objc.classAddMethod(cls, SEL, newMethod)
        return wrapper
    return decorator

@swizzle(MailDocumentEditor, 'isLoaded')
def isLoaded(self, original):
    global isQuoteFixed

    # call superclass method first
    isloaded = original(self)
    if not isloaded or not QFApp().active:
        return isloaded

    # check if this message was already quotefixed
    if self in isQuoteFixed:
        return isloaded

    try:
        # check for the right kind of message:
        #   messagetype == 1 -> reply           (will  be fixed)
        #   messagetype == 2 -> reply to all    (will  be fixed)
        #   messagetype == 3 -> forward         (will  be fixed)
        #   messagetype == 4 -> is draft        (won't be fixed)
        #   messagetype == 5 -> new message     (won't be fixed)
        if self.messageType() not in [1, 2, 3]:
            return isloaded

        # grab composeView instance (this is the WebView which contains the
        # message editor) and check for the right conditions
        composeView = objc.getInstanceVariable(self, 'composeWebView')
        if not composeView or composeView.isLoading() or not composeView.isEditable():
            return isloaded

        # move cursor to end of document and signal that this view was
        # 'fixed', since this method gets called repeatedly (can't use
        # a new instance variable for this since the Obj-C backend doesn't
        # appreciate that)
        composeView.moveToEndOfDocument_(self)
        isQuoteFixed[self] = True

        # perform some more modifications
        backend = self.backEnd()
        message = backend.message()
        is_rich = backend.containsRichText()
        frame   = composeView.mainFrame()
        dom     = frame.DOMDocument()
        root    = dom.documentElement()

        # send original HTML to menu for debugging
        QFApp().html = root.innerHTML()

        ### Start cleaning up

        # remove quotes
        if removeOldQuotes(self, root, composeView):
            # if we changed anything, reset the 'changed' state of the
            # compose backend
            self.backEnd().setHasChanges_(False)

        # remove signature from sender
        if removeOldSignature(self, root, composeView):
            self.backEnd().setHasChanges_(False)

        # place cursor above own signature (if any)
        if moveAboveNewSignature(self, dom, composeView):
            self.backEnd().setHasChanges_(False)
        else:
            composeView.insertNewline_(self)

        # perform some general cleanups
        if cleanupLayout(self, dom, root):
            self.backEnd().setHasChanges_(False)

        # move to beginning of line
        composeView.moveToBeginningOfLine_(self)
    except Exception, e:
        if QFApp().debugging:
            QFAlert.showException(self)
    return isloaded

class QuoteFix(MVMailBundle):

    @classmethod
    def initialize(cls):
        # register ourselves
        MVMailBundle.registerBundle()
        # extract plugin version from Info.plist
        bundle  = NSBundle.bundleWithIdentifier_('name.klep.mail.QuoteFix')
        version = bundle.infoDictionary().get('CFBundleVersion', '??')
        # initialize
        QFApp(version)
        NSLog("QuoteFix Plugin (version %s) registered with Mail.app" % version)
