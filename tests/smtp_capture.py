"""Minimal local SMTP capture server for automated email assertions.

Never relays anything; it only records what the app tried to send.
`fail_rcpt=True` makes it refuse recipients (a real SMTP-level failure).
"""
import socketserver
import threading
from email import message_from_bytes, policy


class _Handler(socketserver.StreamRequestHandler):
    def reply(self, line):
        self.wfile.write((line + "\r\n").encode())

    def handle(self):
        srv = self.server
        srv.connections += 1
        self.reply("220 capture ESMTP")
        rcpts, mail_from = [], None
        while True:
            raw = self.rfile.readline()
            if not raw:
                return
            cmd = raw.decode(errors="replace").strip()
            verb = cmd[:4].upper()
            if verb in ("EHLO", "HELO"):
                self.reply("250-capture" if verb == "EHLO" else "250 capture")
                if verb == "EHLO":
                    self.reply("250 AUTH PLAIN LOGIN")
            elif verb == "AUTH":
                self.reply("235 2.7.0 Authentication successful")
            elif verb == "MAIL":
                mail_from, rcpts = cmd, []
                self.reply("250 OK")
            elif verb == "RCPT":
                if srv.fail_rcpt:
                    self.reply("550 5.1.1 Mailbox unavailable")
                else:
                    rcpts.append(cmd.split(":", 1)[1].strip().strip("<>"))
                    self.reply("250 OK")
            elif verb == "DATA":
                self.reply("354 End data with <CR><LF>.<CR><LF>")
                lines = []
                while True:
                    line = self.rfile.readline()
                    if line in (b".\r\n", b".\n", b""):
                        break
                    lines.append(line[1:] if line.startswith(b"..") else line)
                msg = message_from_bytes(b"".join(lines), policy=policy.default)
                srv.messages.append({"from": mail_from, "rcpts": list(rcpts), "msg": msg})
                self.reply("250 OK queued")
            elif verb in ("RSET", "NOOP"):
                self.reply("250 OK")
            elif verb == "QUIT":
                self.reply("221 Bye")
                return
            else:
                self.reply("502 Command not implemented")


class CaptureServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _Handler)
        self.messages, self.connections, self.fail_rcpt = [], 0, False
        self.port = self.server_address[1]
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def close(self):
        self.shutdown()
        self.server_close()
