import pygame
import sys
import random

# Pygameの初期化
pygame.init()

# 画面サイズとタイルサイズの設定
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32  # タイルのサイズ

# カラー定義
WHITE = (255, 255, 255)

# ウィンドウの設定
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("hunter task")

# マップデータ（20x20のグリッド）
map_data = [[0 for _ in range(20)] for _ in range(20)]

# 画像データ読み込み
ground_img = pygame.image.load("images/ground.png")
ground_img = pygame.transform.scale(ground_img, (TILE_SIZE, TILE_SIZE))

player1_img = pygame.image.load("images/player1.png")
player1_img = pygame.transform.scale(player1_img, (TILE_SIZE, TILE_SIZE))

player2_img = pygame.image.load("images/player2.png")
player2_img = pygame.transform.scale(player2_img, (TILE_SIZE, TILE_SIZE))

prey1_img = pygame.image.load("images/prey1.png")   # 獲物エージェントの画像
prey1_img = pygame.transform.scale(prey1_img, (TILE_SIZE, TILE_SIZE))

prey2_img = pygame.image.load("images/prey2.png")   # 獲物エージェントの画像
prey2_img = pygame.transform.scale(prey2_img, (TILE_SIZE, TILE_SIZE))

# プレイヤー・獲物の初期位置
all_positions = [(x, y) for x in range(len(map_data[0])) for y in range(len(map_data))]
# 重複なしでランダムに座標を決める
player1_pos, player2_pos, prey1_pos, prey2_pos = random.sample(all_positions, 4)
player1_x, player1_y = player1_pos
player2_x, player2_y = player2_pos
prey1_x, prey1_y = prey1_pos
prey2_x, prey2_y = prey2_pos

# 動き判定
#moved1 = False
#moved2 = False
hunt1 = False
hunt2 = False

# ウィンドウに表示する文字の設定
font1 = pygame.font.SysFont(None, 30)
message_hunt = "Preys are Not hunted"
text_hunt = font1.render(message_hunt, True, (255, 0, 0))

message_count = "Count : 0"
text_count = font1.render(message_count, True, (255, 0, 0))


# 移動回数
count = 0

# 意図推定から行動決定までLLMにやらせる？


# マップ生成
def draw_map():
    for row in range(len(map_data)):
        for col in range(len(map_data[row])):
            tile = map_data[row][col]
            if tile == 0:
                screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(player_img, x, y):
    screen.blit(player_img, (x * TILE_SIZE, y * TILE_SIZE))

def draw_prey(prey_img, x, y):
    screen.blit(prey_img, (x * TILE_SIZE, y * TILE_SIZE))

def move_prey(prey_x, prey_y):
    r = random.random()  # 0.0〜1.0 の乱数
    if r < 0.2:  # 20%で上に移動
        prey_y -= 1
        if prey_y  < 0:
            prey_y = len(map_data) - 1
    elif r < 0.6:  # 40%で右に移動
        prey_x += 1
        if prey_x  > len(map_data[0]) - 1:
            prey_x = 0
    else:  # 40%は動かない
        pass

    return prey_x, prey_y

# メインループ
clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        moved1 = False
        

        # プレイヤー移動（キー入力）
        if event.type == pygame.KEYDOWN:
            
            
            # プレイヤー1の操作
            if event.key == pygame.K_UP:
                player1_y -= 1
                if player1_y  < 0:
                    player1_y = len(map_data) - 1
                moved1 = True
            if event.key == pygame.K_DOWN:
                player1_y += 1
                if player1_y > len(map_data) - 1:
                    player1_y = 0
                moved1 = True
            if event.key == pygame.K_LEFT:
                player1_x -= 1
                if player1_x < 0:
                    player1_x = len(map_data[0]) - 1
                moved1 = True
            if event.key == pygame.K_RIGHT:
                player1_x += 1
                if player1_x > len(map_data[0]) - 1:
                    player1_x = 0
                moved1 = True
            if event.key == pygame.K_SPACE:
                moved1 = True

            # プレイヤー2の動き
            if moved1:
                r_2 = random.random()
                if r_2 < 0.2:
                    player2_y -= 1
                    if player2_y  < 0:
                        player2_y = len(map_data) - 1
                elif r_2 < 0.4:
                    player2_y += 1
                    if player2_y > len(map_data) - 1:
                        player2_y = 0
                elif r_2 < 0.6:
                    player2_x -= 1
                    if player2_x < 0:
                        player2_x = len(map_data[0]) - 1
                elif r_2 < 0.8:
                    player2_x += 1
                    if player2_x > len(map_data[0]) - 1:
                        player2_x = 0
                else:
                    pass
            
                # 捕獲判定
                if not hunt1:  # prey1 がまだ捕まっていないときだけチェック
                    same_pos_prey1 = (player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y)
                    if same_pos_prey1:
                        hunt1 = True

                if not hunt2:  # prey2 がまだ捕まっていないときだけチェック
                    same_pos_prey2 = (player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y)
                    if same_pos_prey2:
                        hunt2 = True

                # 両方の獲物が同じマスで、かつハンターもそのマスにいる場合 → 両方捕まる
                if (prey1_x, prey1_y) == (prey2_x, prey2_y) and same_pos_prey1 and same_pos_prey2:
                    hunt1, hunt2 = True, True
                else:
                    # prey1 が捕まる（ただしまだ捕まっていない場合のみ）
                    if not hunt1 and same_pos_prey1:
                        hunt1 = True

                    # prey2 が捕まる（ただしまだ捕まっていない場合のみ）
                    if not hunt2 and same_pos_prey2:
                        hunt2 = True
                
            
                # 獲物がハンターに捕まっていると動けなくなる
            
                if not hunt1:
                    prey1_x, prey1_y = move_prey(prey1_x, prey1_y)

                if not hunt2:
                    prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

                # countもハンターが二体とも動いたときにのみ増やすようにしたい→すべて同時に動く前提からして不要かも
                # 獲物が二体とも捕まるとカウントを止める
                if (not hunt1) or (not hunt2):
                    count += 1

           

            
            
                message_hunt = "Preys are " + ("HUNTED!" if (hunt1 and hunt2) else "Not hunted")
                text_hunt = font1.render(message_hunt, True, (255, 0, 0))

                message_count = "Count : " + str(count)
                text_count = font1.render(message_count, True, (255, 0, 0))
            

    # 描画
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)
    screen.blit(text_hunt, (670, 10))
    screen.blit(text_count, (670, 50))
    pygame.display.flip()
    

    clock.tick(30)  # 30fpsで描画（ただし獲物はプレイヤー移動時しか動かない）
