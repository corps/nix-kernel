from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
import pexpect

from subprocess import check_output
import os.path

import re
import signal

__version__ = '0.1.0'

version_pat = re.compile(r'\(Nix\) (\d+(\.\d+)+)')
error_message = re.compile(r'^error\:\ ', re.MULTILINE)

class IncrementalOutputWrapper(replwrap.REPLWrapper):
    def __init__(self, cmd_or_spawn, orig_prompt, prompt_change,
                 line_output_callback=None, **kwds):
        self.line_output_callback = line_output_callback
        replwrap.REPLWrapper.__init__(self, cmd_or_spawn, orig_prompt,
                                      prompt_change, **kwds)

    def _expect_prompt(self, timeout=-1):
        if timeout == None:
            # "None" means we are executing code from a Jupyter cell by way of the run_command
            # in the do_execute() code below, so do incremental output.
            while True:
                pos = self.child.expect_exact([self.prompt, self.continuation_prompt, u'\r\n'],
                                              timeout=None)
                if pos == 2:
                    # End of line received
                    self.line_output_callback(self.child.before + '\n')
                else:
                    if len(self.child.before) != 0:
                        # prompt received, but partial line precedes it
                        self.line_output_callback(self.child.before)
                    break
        else:
            # Otherwise, use existing non-incremental code
            pos = replwrap.REPLWrapper._expect_prompt(self, timeout=timeout)

        # Prompt received, so return normally
        return pos

class NixKernel(Kernel):
    implementation = 'nix-kernel'
    implementation_version = __version__

    @property
    def language_version(self):
        m = version_pat.search(self.banner)
        return m.group(1)

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(['nix', 'repl', '--version']).decode('utf-8')
        return self._banner

    language_info = {'name': 'nix',
                     'mimetype': 'text/nix',
                     'file_extension': '.nix'}

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_repl()

    def _start_repl(self):
        # Signal handlers are inherited by forked processes, and we can't easily
        # reset it from the subprocess. Since kernelapp ignores SIGINT except in
        # message handlers, we need to temporarily reset the SIGINT handler here
        # so that bash and its children are interruptible.
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            child = pexpect.spawn('nix repl', [], echo=False, encoding='utf-8', codec_errors='replace')
            prompt       = u'nix-repl> '
            continuation = u'          '
            self.wrapper = IncrementalOutputWrapper(child, prompt, None,
                                        new_prompt=prompt,
                                        continuation_prompt=continuation,
                                        line_output_callback=self.process_output)
        finally:
            signal.signal(signal.SIGINT, sig)

    def process_output(self, output):
        if not self.error_result:
            m = error_message.search(output)
            if m:
                self.error_result = output[m.start():]
                output = output[:m.start()]

            if not self.silent:
                # Send standard output
                stream_content = {'name': 'stdout', 'text': output}
                self.send_response(self.iopub_socket, 'stream', stream_content)
        else:
            self.error_result += u"\r\n" + output

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        self.silent = silent
        self.error_result = u""
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False
        try:
            self.wrapper.run_command(code.rstrip(), timeout=None)
        except KeyboardInterrupt:
            self.wrapper.child.sendintr()
            self.wrapper._expect_prompt()
            output = self.wrapper.child.before
            self.process_output(output)
            return {'status': 'abort', 'execution_count': self.execution_count}
        except EOF:
            output = self.wrapper.child.before + 'Restarting nix-repl'
            self._start_repl()
            self.process_output(output)

        if self.error_result:
            error_content = {'execution_count': self.execution_count,
                             'ename': 'ExecutionErr', 'evalue': "", 'traceback':
                             self.error_result.split("\r\n")}

            self.send_response(self.iopub_socket, 'error', error_content)
            error_content['status'] = 'error'
            return error_content
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

    def do_complete(self, code, cursor_pos):
        return {'matches': [], 'cursor_start': 0,
                   'cursor_end': cursor_pos, 'metadata': dict(),
                   'status': 'ok'}
