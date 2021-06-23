import gym
import pyglet
from simple_websocket_server import WebSocketServer, WebSocket
from gym.envs.classic_control import rendering 
import time
import ssl

class TransmiterHandler (WebSocket):
    linked = False
    got_message = False
    message = ""
    def handle(self):
        self.got_message = True
        self.message = self.data
        print(self.address, 'got replied:')
        print(self.message)
        print(self.address, '[end of message]')

    def connected(self):
        self.linked = True
        print(self.address, 'connected')

    def handle_close(self):
        self.linked = False
        print(self.address, 'closed')


class TanksEnv(gym.Env):
    
    def __init__(self):
        super().__init__()
        print("[TANKS ENVIRONMENT] Waiting for client connection...")
        self.server = WebSocketServer('', 9090, TransmiterHandler, None, None, ssl.PROTOCOL_TLSv1, 0.0001)
        if (self._waitForConnection()):
            print("[TANKS ENVIRONMENT] Got connection and ready!")

    def _waitForConnection(self):
        hasConnection = False
        while not hasConnection:
            self.server.handle_request()
            for desc, conn in self.server.connections.items():
                if (conn.linked):
                    hasConnection = True
                    break
            if (hasConnection):
                self.server.handle_request()
        return True

    def _sendMessageToClients(self, message):
        for desc, conn in self.server.connections.items():
            conn.send_message(message)
        self.server.handle_request()

    def _closeConnection(self):
        for desc, conn in self.server.connections.items():
            conn.close()
        hasConnection = True
        while (hasConnection):
            self.server.handle_request()
            hasConnection = False
            for desc, conn in self.server.connections.items():
                if (conn.linked):
                    hasConnection = True
                    break

    # reset environment by reloading browser and establishing connection again
    def reset(self):
        print("[TANKS] Reloading...")
        self._closeConnection()
        print("[TANKS] Close all connections.")
        print("[TANKS] Reconnecting ...")
        self._waitForConnection()
        print("[TANKS] Few, got a new connection. Reset Completed!")

    def step(self, action):
        start_clock = time.time()
        print("[TANKS ENVIRONMENT] Next Step...")

        for desc, conn in self.server.connections.items():
            conn.send_message("STEP")

        while (True):
            self.server.handle_request()
            hasReplied = False
            for desc, conn in self.server.connections.items():
                if (conn.got_message):
                    hasReplied = True
                    conn.got_message = False
                    break
            if (hasReplied):
                self.server.handle_request()
                break
            
        elapsed = time.time() - start_clock
        print("[TANKS ENVIRONMENT] Next Step Completed! (", elapsed, "seconds)")
    

    # def render(self):


    def close(self):
        self.server.close()
        print("[TANKS] Closed.")

if __name__ == "__main__":

    # def key_press(k, mod):
        # for desc, conn in server.connections.items():
        #     conn.send_message("Hello, Client!")
    
    viewer = rendering.Viewer(400, 300)

    env = TanksEnv()
    env.reset()
    
    while (True):
        for i in range(60 * 10):
            viewer.window.switch_to()
            viewer.window.dispatch_events()
            env.step(None)
            time.sleep(0.001)
        env.reset()

    env.close()