import threading
# import random
import bottle
import shutil

class HTTPServer():
    def __init__(self, manager, id, 
                 host='127.0.0.1', port=8080):

        self.id = id
        self.manager = manager

        self.host = host
        self.port = port

        self.app = bottle.Bottle()
        
        @self.app.get('/')
        def question_debut():
            return bottle.template('static/question_debut.tpl', id=self.id)


        @self.app.get('/control')			
        def control():
            return bottle.static_file('control.html', root='./static')

        @self.app.get('/scene/<name>')
        def load_scene(name):
            print 'load scene', name            
            return bottle.static_file('control.html', root='./static')

        
        @self.app.get('/')
        @self.app.get('/game/')
        def game():
            return bottle.static_file('game.html', root='./static')
			
			


	
        @self.app.get('/game/start/<dummy:int>')
        def start_game(dummy):
            self.manager.realswitch_game(self.manager.next_gameid)
            return bottle.static_file('game.html', root='./static')
        
        # @self.app.get('/questionnaire/fin')
        # def question_fin():
        #     self.manager.switch_game(-1)
        #     return bottle.template('static/question_fin.tpl', id=self.id, dummy=random.randint(0, 1000000000000))
            
        # @self.app.get('/questionnaire/finpretest/<dummy:int>')
        # def question_finpretest(dummy):
        #     return bottle.template('static/question_finpretest.tpl', id=self.id, dummy=dummy)
            
            
        @self.app.get('/questionnaire/fin')
        @self.app.get('/byebye/<dummy:int>')
        def byebye(dummy=42):
            self.manager.should_stop = True
            return bottle.static_file('bye.html', root='./static')
            
            
        @self.app.get('/realswitch/<game_id:int>')
        def real_switch(game_id):
                        
            real_game_id = self.manager.game2id[game_id - 1]            
            g = self.manager.games[real_game_id]
            
            if hasattr(g, 'image_filename'):
                shutil.copyfile(g.image_filename, 'static/game_{}.jpg'.format(game_id))
            self.manager.realswitch_game(real_game_id)
        
        @self.app.get('/switch/<game_id:int>')
        def switch(game_id):
        
            real_game_id = self.manager.game2id[game_id - 1]            
            g = self.manager.games[real_game_id]
        
            if hasattr(g, 'image_filename'):
                shutil.copyfile(g.image_filename, 'static/game_{}.jpg'.format(game_id))
            self.manager.switch_game(real_game_id)
            
        
        @self.app.get('/static/:filename#.*#')
        def send_static(filename):
            return bottle.static_file(filename, root='./static/')

    def start(self):
        print 'starting server on', self.host, self.port
        t = threading.Thread(target=lambda: bottle.run(self.app,
                                                       host=self.host, port=self.port,
                                                       quiet=True,
                                                       server='tornado',   
                                                       debug=True))
        t.daemon = True
        t.start()
    

    
