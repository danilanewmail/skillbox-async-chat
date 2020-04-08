#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()


        if self.login is not None:
            if decoded.replace("\r\n", ""):
                self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                temp_login = decoded.replace("login:", "").replace("\r\n", "")
                if self.check_login(temp_login):
                    self.login = temp_login
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.server.send_history(self)
                else:
                    self.transport.write(
                        f"Логин {temp_login} занят, попробуйте другой\n".encode()
                    )
                    self.transport.close()
            else:
                if decoded.replace("\r\n", ""):
                    self.transport.write("Неправильный логин\n".encode())



    def check_login(self, login):
        for user in self.server.clients:
            if user.login == login:
                return False
        return True

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.add_to_history(message)
        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def add_to_history(self, message):
        if len(self.history) > 9:
            self.history.pop(0)
        self.history.append(message)

    def send_history(self, current_protocol: ServerProtocol):
        for message in self.history:
            current_protocol.transport.write(message.encode())


    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
