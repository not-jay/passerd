import re

class Dialog:
    """An abstract interface to "user dialogs"
    """
    def __init__(self, *args, **kwargs):
        self.patterns = []
        self.dialog_init(*args, **kwargs)
        self.message_func = None

    def set_message_func(self, fn):
        self.message_func = fn

    def dialog_init(self, *args, **kwargs):
        """Initialize the Dialog object"""
        pass

    def begin(self):
        """Start the dialog"""
        pass

    def wait_for(self, regexp, func, flags=re.I, strip=True):
        if strip:
            filter = (lambda s: s.strip())
        else:
            filter = (lambda s: s)

        self.patterns.insert(0, (filter, re.compile(regexp, flags), func) )

    def recv_message(self, msg):
        for filter,expr,func in self.patterns:
            s = filter(msg)
            m = expr.search(s)
            if m:
                try:
                    func(msg, m)
                except Exception,e:
                    self.message("An error has occurred. Sorry. -- %s" % (e))
                return
        self.message("Sorry, I don't know what you mean")

    def message(self, msg):
        """Send a message to the user"""
        if self.message_func is None:
            raise NotImplementedError("Dialog.message: not message_func set")
        return self.message_func(msg)


class CommandDialog(Dialog):
    """A dialog for simple 'command args' commands"""
    def unknown_command(self, cmd, args):
        #TODO: show help
        self.message("Sorry, I don't get it.")

    def recv_message(self, msg):
        parts = msg.split(' ',1)
        cmd = parts[0]
        cmd = cmd.lower()
        args = parts[1:]
        fn = getattr(self, 'command_%s' % (cmd), None)
        if fn is None:
            return self.unknown_command(cmd, args)
        return fn(args)



def attach_dialog_to_channel(dialog, chan, bot_user):
    def doit():
        chan.add_msg_notifier(got_chan_msg)
        dialog.set_message_func(send_message)

    def got_chan_msg(ch, sender, msg):
        assert ch is chan
        dialog.recv_message(msg)

    def send_message(msg):
        chan.send_message(bot_user, msg)

    doit()

def attach_dialog_to_bot(dialog, proto, real_user, bot):
    def doit():
        bot.add_msg_notifier(got_msg)
        dialog.set_message_func(send_message)

    def got_msg(u, sender, msg):
        assert u is bot
        dialog.recv_message(msg)

    def send_message(msg):
        proto.send_notice(bot, real_user, msg)

    doit()
