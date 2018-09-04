import logging
from typing import List, Callable
from datetime import datetime

import requests
import vk


class Event:
    __slots__ = ('type', 'object', 'group_id', 'time_created')

    def __init__(self, json: dict = None):
        if json:
            self.time_created = datetime.now()  # type: datetime
            self.type = json.get('type')  # type: str
            self.object = json.get('object')  # type: dict
            self.group_id = json.get('group_id')  # type: int


class Rule:
    """
    Rule object is used to check if a Message objects suits under needed requirements.
    It should be inherited and used passed to Handler
    """

    def __init__(self):
        pass

    def check(self, event: Event):
        raise NotImplementedError("check() is not implemented in {0}" % self.__class__.__name__)


class TypeRule(Rule):
    # noinspection PyMissingConstructor
    def __init__(self, event_type: str, func: Callable = None):
        self.type = event_type
        self.function = func

    def check(self, event: Event):
        if self.type == event.type:
            if self.function:
                return self.function(event)
            else:
                return True
        return False


class MessageRule(Rule):
    __slots__ = ('attachment_types', 'payload', 'func_text', 'func_msg', 'regexp', 'commands')

    # noinspection PyMissingConstructor
    def __init__(self, attachment_types: list = None, payload: dict = None, func_text: Callable = None,
                 func_msg: Callable = None, regexp: str = None, commands: list = None):
        self.attachment_types = attachment_types
        self.payload = payload
        self.func_text = func_text
        self.func_msg = func_msg
        self.regexp = regexp
        self.commands = commands

    def check(self, event: Event):
        if event.type == 'message_new':
            msg = event.object
            check = False
            if self.attachment_types:
                check |= any([i['type'] in self.attachment_types for i in msg.get('attachments')])
            if self.payload:
                check |= msg.get('payload', {}) == self.payload
            if self.func_text:
                check |= self.func_text(event)
            if self.func_msg:
                check |= self.func_msg(event)
            if self.regexp:
                import re
                check |= re.match(self.regexp, msg['text'])
            if self.commands:
                for command in self.commands:
                    check |= command in msg['text']
            return check
        else:
            return False


class Handler:
    __slots__ = ('func', 'rule')

    def __init__(self, func, rule: Rule):
        self.func = func
        self.rule = rule

    def handle(self, ev: Event):
        if self.rule.check(ev):
            self.func(ev)
            return True
        else:
            return False


class VKBot:
    _handlers = []  # type: List[Handler]

    def __init__(self, api: vk.API, group_id: int, v: str = '5.80',
                 logger: logging.Logger = logging.getLogger("VKBot")):
        self.v = v
        self.api = api
        self.logger = logger
        self.group_id = group_id

    def handle_message(self, **message_rule_args):
        def handle_message_decorator(func):
            self._handlers.append(Handler(func, MessageRule(**message_rule_args)))
            return func

        return handle_message_decorator

    def handle_event(self, rule: Rule = None, event_type: str = None):
        def handle_message_decorator(func):
            if rule:
                self._handlers.append(Handler(func, rule))
            else:
                self._handlers.append(Handler(func, TypeRule(event_type)))
            return func

        return handle_message_decorator

    def run(self, threaded=False, reload=False):
        logger = self.logger
        while True:
            logger.info("Getting new longpoll server")
            s = self.api.groups.getLongPollServer(group_id=self.group_id)
            logger.debug("getLongPollServer returned " + repr(s))
            ts = s['ts']
            url = "{server}?act=a_check&key={key}&ts={{ts}}&wait=25".format(server=s['server'], key=s['key'])
            while True:
                logger.debug("Getting updates")
                rq = requests.get(url.format(ts=ts)).json()
                if rq.get('failed'):
                    logger.error("LongPoll failed. Code: {0}".format(rq['failed']))
                    if rq['failed'] == 1:
                        continue
                    else:
                        break

                updates = rq.get('updates', [])
                logger.debug("Got {0} new updates".format(len(updates)))

                from itertools import count
                for i, event in zip(count(), updates):
                    logger.debug("Processing update {0}: {1}".format(i, event))
                    ev = Event(event)
                    for handler in self._handlers:
                        if handler.handle(ev):
                            break
                    else:
                        logger.warning("Event {0} wasn't processed by any handler. "
                                       "You should unsubscribe from such events in group settings".format(ev.type))

                ts = rq.get('ts', 1)
            if not reload:
                logger.info("Shutting down.")
                break
        pass
