# process/ipc_handler.py
"""
Gestionnaire de communication inter-processus (IPC) sécurisée
entre le panneau de contrôle et l'application OptimPV
"""

import socket
import json
import threading
import time
import struct
import secrets
from typing import Dict, Optional, Callable, Any
from datetime import datetime

from security.crypto_store import SecureStorage
from utils.logger import SecureLogger


class SecureIPC:
    """Communication IPC sécurisée via sockets TCP locaux"""
    
    def __init__(self):
        self.logger = SecureLogger()
        self.crypto = SecureStorage()
        
        # Serveur
        self.server_socket = None
        self.server_thread = None
        self.server_port = None
        self._server_running = False
        
        # Client
        self.client_socket = None
        self.connected_clients = {}
        
        # Callbacks
        self._message_handlers = {}
        self._connection_callback = None
        
        # Sécurité
        self._auth_tokens = {}
        self._rate_limits = {}
    
    def start_server(self, port: int = 0) -> int:
        """
        Démarrer serveur IPC
        
        Args:
            port: Port à utiliser (0 = auto)
            
        Returns:
            Port utilisé
        """
        try:
            # Créer socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind sur localhost uniquement
            self.server_socket.bind(('127.0.0.1', port))
            self.server_socket.listen(5)
            
            # Obtenir port assigné
            self.server_port = self.server_socket.getsockname()[1]
            
            # Démarrer thread serveur
            self._server_running = True
            self.server_thread = threading.Thread(
                target=self._server_loop,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.log_event('IPC_SERVER_STARTED', {
                'port': self.server_port
            })
            
            return self.server_port
            
        except Exception as e:
            self.logger.log_event('IPC_SERVER_START_ERROR', {
                'error': str(e)
            })
            raise
    
    def stop_server(self):
        """Arrêter serveur IPC"""
        self._server_running = False
        
        # Fermer connexions clients
        for client_id, client_info in list(self.connected_clients.items()):
            try:
                client_info['socket'].close()
            except:
                pass
        
        self.connected_clients.clear()
        
        # Fermer socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        self.logger.log_event('IPC_SERVER_STOPPED', {})
    
    def connect_to_server(self, host: str, port: int, auth_token: str) -> bool:
        """
        Se connecter à un serveur IPC
        
        Args:
            host: Adresse du serveur
            port: Port du serveur
            auth_token: Token d'authentification
            
        Returns:
            Success
        """
        try:
            # Créer socket client
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            
            # Connecter
            self.client_socket.connect((host, port))
            
            # Authentifier
            auth_msg = {
                'type': 'auth',
                'token': auth_token,
                'timestamp': datetime.now().isoformat()
            }
            
            self._send_message(self.client_socket, auth_msg)
            
            # Attendre réponse
            response = self._receive_message(self.client_socket)
            
            if response and response.get('status') == 'authenticated':
                self.logger.log_event('IPC_CLIENT_CONNECTED', {
                    'server': f"{host}:{port}"
                })
                return True
            else:
                self.client_socket.close()
                self.client_socket = None
                return False
                
        except Exception as e:
            self.logger.log_event('IPC_CLIENT_CONNECT_ERROR', {
                'error': str(e)
            })
            return False
    
    def send_command(self, command: Dict, timeout: float = 5.0) -> Optional[Dict]:
        """
        Envoyer commande et attendre réponse
        
        Args:
            command: Commande à envoyer
            timeout: Timeout pour la réponse
            
        Returns:
            Réponse ou None
        """
        if not self.client_socket:
            return None
        
        try:
            # Ajouter ID unique
            command['id'] = secrets.token_hex(8)
            command['timestamp'] = datetime.now().isoformat()
            
            # Envoyer
            self._send_message(self.client_socket, command)
            
            # Attendre réponse avec timeout
            self.client_socket.settimeout(timeout)
            response = self._receive_message(self.client_socket)
            
            # Vérifier ID correspond
            if response and response.get('reply_to') == command['id']:
                return response
            else:
                return None
                
        except socket.timeout:
            self.logger.log_event('IPC_COMMAND_TIMEOUT', {
                'command': command.get('action')
            })
            return None
        except Exception as e:
            self.logger.log_event('IPC_COMMAND_ERROR', {
                'error': str(e)
            })
            return None
    
    def register_handler(self, message_type: str, handler: Callable):
        """Enregistrer handler pour type de message"""
        self._message_handlers[message_type] = handler
    
    def set_connection_callback(self, callback: Callable):
        """Définir callback pour nouvelles connexions"""
        self._connection_callback = callback
    
    def broadcast_message(self, message: Dict):
        """Diffuser message à tous les clients connectés"""
        for client_id, client_info in list(self.connected_clients.items()):
            try:
                self._send_message(client_info['socket'], message)
            except:
                # Client déconnecté
                self._handle_client_disconnect(client_id)
    
    def _server_loop(self):
        """Boucle principale du serveur"""
        while self._server_running:
            try:
                # Accepter connexions
                self.server_socket.settimeout(1)
                
                try:
                    client_socket, client_addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                
                # Gérer nouvelle connexion dans thread séparé
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_addr),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self._server_running:
                    self.logger.log_event('IPC_SERVER_ERROR', {
                        'error': str(e)
                    })
    
    def _handle_client(self, client_socket: socket.socket, client_addr: tuple):
        """Gérer connexion client"""
        client_id = secrets.token_hex(8)
        authenticated = False
        
        try:
            # Attendre authentification
            client_socket.settimeout(5)
            auth_msg = self._receive_message(client_socket)
            
            if auth_msg and auth_msg.get('type') == 'auth':
                # Vérifier token
                if self._verify_auth_token(auth_msg.get('token')):
                    authenticated = True
                    
                    # Enregistrer client
                    self.connected_clients[client_id] = {
                        'socket': client_socket,
                        'address': client_addr,
                        'auth_time': datetime.now(),
                        'last_activity': datetime.now()
                    }
                    
                    # Répondre succès
                    self._send_message(client_socket, {
                        'status': 'authenticated',
                        'client_id': client_id
                    })
                    
                    # Callback connexion
                    if self._connection_callback:
                        self._connection_callback(client_id, client_addr)
                    
                    self.logger.log_event('IPC_CLIENT_AUTHENTICATED', {
                        'client_id': client_id,
                        'address': f"{client_addr[0]}:{client_addr[1]}"
                    })
                else:
                    # Auth échouée
                    self._send_message(client_socket, {
                        'status': 'auth_failed'
                    })
                    client_socket.close()
                    return
            
            # Si authentifié, gérer messages
            if authenticated:
                client_socket.settimeout(None)
                
                while self._server_running:
                    message = self._receive_message(client_socket)
                    
                    if not message:
                        break
                    
                    # Mettre à jour activité
                    self.connected_clients[client_id]['last_activity'] = datetime.now()
                    
                    # Rate limiting
                    if not self._check_rate_limit(client_id):
                        self._send_message(client_socket, {
                            'error': 'rate_limit_exceeded'
                        })
                        continue
                    
                    # Traiter message
                    response = self._process_message(message, client_id)
                    
                    if response:
                        response['reply_to'] = message.get('id')
                        self._send_message(client_socket, response)
                        
        except Exception as e:
            self.logger.log_event('IPC_CLIENT_ERROR', {
                'client_id': client_id,
                'error': str(e)
            })
        finally:
            # Nettoyer
            self._handle_client_disconnect(client_id)
            try:
                client_socket.close()
            except:
                pass
    
    def _process_message(self, message: Dict, client_id: str) -> Optional[Dict]:
        """Traiter message reçu"""
        msg_type = message.get('type') or message.get('action')
        
        # Handler enregistré
        if msg_type in self._message_handlers:
            try:
                return self._message_handlers[msg_type](message, client_id)
            except Exception as e:
                self.logger.log_event('IPC_HANDLER_ERROR', {
                    'type': msg_type,
                    'error': str(e)
                })
                return {'error': 'handler_error'}
        
        # Handlers par défaut
        if msg_type == 'ping':
            return {'type': 'pong', 'timestamp': datetime.now().isoformat()}
        
        elif msg_type == 'health_check':
            return {
                'status': 'healthy',
                'uptime': time.time(),
                'clients': len(self.connected_clients)
            }
        
        else:
            return {'error': 'unknown_message_type'}
    
    def _send_message(self, sock: socket.socket, message: Dict):
        """Envoyer message via socket"""
        # Sérialiser
        data = json.dumps(message, ensure_ascii=False).encode('utf-8')
        
        # Chiffrer si nécessaire
        # data = self.crypto.encrypt_data(data)
        
        # Envoyer taille puis données
        size = len(data)
        sock.sendall(struct.pack('!I', size))
        sock.sendall(data)
    
    def _receive_message(self, sock: socket.socket) -> Optional[Dict]:
        """Recevoir message via socket"""
        try:
            # Recevoir taille
            size_data = self._recv_all(sock, 4)
            if not size_data:
                return None
            
            size = struct.unpack('!I', size_data)[0]
            
            # Limite de sécurité
            if size > 1024 * 1024:  # 1MB max
                return None
            
            # Recevoir données
            data = self._recv_all(sock, size)
            if not data:
                return None
            
            # Déchiffrer si nécessaire
            # data = self.crypto.decrypt_data(data)
            
            # Désérialiser
            return json.loads(data.decode('utf-8'))
            
        except Exception:
            return None
    
    def _recv_all(self, sock: socket.socket, size: int) -> Optional[bytes]:
        """Recevoir exactement 'size' bytes"""
        data = b''
        
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        
        return data
    
    def _verify_auth_token(self, token: str) -> bool:
        """Vérifier token d'authentification"""
        # TODO: Implémenter vérification réelle
        # Pour l'instant, accepter tous les tokens non vides
        return bool(token)
    
    def _check_rate_limit(self, client_id: str) -> bool:
        """Vérifier limite de taux pour client"""
        current_time = time.time()
        
        if client_id not in self._rate_limits:
            self._rate_limits[client_id] = {
                'count': 0,
                'window_start': current_time
            }
        
        rate_info = self._rate_limits[client_id]
        
        # Reset fenêtre si expirée (1 minute)
        if current_time - rate_info['window_start'] > 60:
            rate_info['count'] = 0
            rate_info['window_start'] = current_time
        
        # Incrémenter et vérifier
        rate_info['count'] += 1
        
        # Limite: 100 messages/minute
        return rate_info['count'] <= 100
    
    def _handle_client_disconnect(self, client_id: str):
        """Gérer déconnexion client"""
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
            
            self.logger.log_event('IPC_CLIENT_DISCONNECTED', {
                'client_id': client_id
            })# Gestion de la communication inter-processus (IPC) 