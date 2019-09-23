import requests

url = 'http://localhost:8000'


def start(user, problem, count):
    uri = url + '/start' + '/' + user + '/' + str(problem) + '/' + str(count)
    return requests.post(uri).json()


def oncalls(token):
    uri = url + '/oncalls'
    return requests.get(uri, headers={'X-Auth-Token': token}).json()


def action(token, cmds):
    uri = url + '/action'
    return requests.post(uri, headers={'X-Auth-Token': token}, json={'commands': cmds}).json()


def p0_simulator():
    user = 'token'
    problem = 2
    count = 1
    max_people = 8
    cur_people = 0
    max_height = 25

    dir = 'UP'

    ret = start(user, problem, count)
    token = ret['token']
    print('Token for %s is %s' % (user, token))

    while True:
        res = oncalls(token)
        print(f'res : {res}')

        if (res['is_end']):
            break

        ### 엘리베이터 안에 승객이 아무도 없고 call도 아무것도 없으면 엘리베이터를 정지시킨다. ###
        if len(res['calls']) == 0 and len(res['elevators'][0]['passengers']) == 0:
            action(token, [{'elevator_id': 0, 'command': 'STOP'}])
            continue
        #####################################################################################

        cur = res['elevators'][0]['floor']
        passengers = res['elevators'][0]['passengers']
        status = res['elevators'][0]['status']
        calls = res['calls']

        # 엘리베이터가 멈춰있는 상태라면
        if status == 'STOPPED':

            ########## 승강기 안에 사람이 있다면 내리는지 검사 ######
            opened = False
            for passenger in passengers:
                if cur == passenger['end']:
                    action(token, [{'elevator_id': 0, 'command': 'OPEN'}])
                    opened = True
                    break
            if opened:
                continue
            ########################################################
            if cur_people < max_people:
                ######### 고객 call 중에 현재 위치에서 call 한 사람이 있다면 OPEN ########
                opened = False
                for call in calls:
                    if cur == call['start']:
                        action(token, [{'elevator_id': 0, 'command': 'OPEN'}])
                        opened = True
                        break

                if opened:
                    continue
            ########################################################################

            ''' 여기까지 왔다면, 내리는 사람도 없고, 현재 위치에서 타는 사람도 없다.'''
            # 다음 승객 위치로 이동해야함. or 다음 기다리는 승객 위치로 이동해야함.
            # 기존에 이동하던 방향으로 엘리베이터 이동
            if dir == 'UP':
                action(token, [{'elevator_id': 0, 'command': 'UP'}])
            else:
                action(token, [{'elevator_id': 0, 'command': 'DOWN'}])

        elif status == 'UPWARD':

            ############ 한 층 올라왔는데 가장 높은 곳이라면 무조건 멈춘다. ########
            if cur == max_height:
                dir = 'DOWN'
                action(token, [{'elevator_id': 0, 'command': 'STOP'}])
                continue

            ###################################################################

            ############# 승강기가 올라간 층에 승객이 내리는지 검사 #############
            stopped = False
            for passenger in passengers:
                # 한 명이라도 내리는 사람이 있다면 엘리베이터를 멈춤
                if cur == passenger['end']:
                    action(token, [{'elevator_id': 0, 'command': 'STOP'}])
                    stopped = True
                    break
            if stopped:
                continue
            ###################################################################

            ############## 현재 층에 탈 사람이 있다면 멈춘다. ####################
            stopped = False
            if cur_people < max_people:
                for call in calls:
                    if cur == call['start']:
                        # 올라가는 사람만 태운다
                        if (call['end'] - call['start'] > 0):
                            action(token, [{'elevator_id': 0, 'command': 'STOP'}])
                            stopped = True
                            break
                if stopped:
                    continue

            ######################################################################
            dir = 'UP'
            action(token, [{'elevator_id': 0, 'command': 'UP'}])

        elif status == 'DOWNWARD':
            ############ 한 층 내려갔는데 가장 낮은 곳이라면 무조건 멈춘다. ########
            if cur == 1:
                dir = 'UP'
                action(token, [{'elevator_id': 0, 'command': 'STOP'}])
                continue
            ###################################################################

            ############# 승강기가 내려간간 층에 승객이 내리는 검 #############
            stopped = False
            for passenger in passengers:
                # 한 명이라도 내리는 사람이 있다면 엘리베이터를 멈춤
                if cur == passenger['end']:
                    action(token, [{'elevator_id': 0, 'command': 'STOP'}])
                    stopped = True
                    break
            if stopped:
                continue
            ###################################################################

            ############## 현재 층에 탈 사람이 있다면 멈춘다. ####################
            stopped = False
            if cur_people < max_people:
                for call in calls:
                    if cur == call['start']:
                        # 내려가는 사람만 태운다
                        if (call['start'] - call['end'] > 0):
                            action(token, [{'elevator_id': 0, 'command': 'STOP'}])
                            stopped = True
                            break
                if stopped:
                    continue

            ######################################################################
            dir = 'DOWN'
            action(token, [{'elevator_id': 0, 'command': 'DOWN'}])


        elif status == 'OPENED':

            ############# 엘리베이터 문이 열려있고 승객 중에 내릴 사람은 내린다. ###########
            call_ids = []
            for passenger in passengers:
                if cur == passenger['end']:
                    call_ids.append(passenger['id'])

            if len(call_ids) > 0:
                cur_people -= len(call_ids)
                action(token, [{'elevator_id': 0, 'command': 'EXIT', 'call_ids' : call_ids}])
                continue
            ######################################################################

            ############ 엘리베이터 문이 열려있고 밖에서 기다리는 사람이 있으면 엘리베이터를 탄다. ###########
            call_ids = []
            for call in calls:
                if cur == call['start']:
                    if cur_people < max_people:
                        cur_people += 1
                        call_ids.append(call['id'])
                    else:
                        break

            if len(call_ids) > 0:
                action(token, [{'elevator_id': 0, 'command': 'ENTER', 'call_ids': call_ids}])
                continue
            ###################################################################################################

            action(token, [{'elevator_id':0, 'command':'CLOSE'}])


if __name__ == '__main__':
    p0_simulator()
