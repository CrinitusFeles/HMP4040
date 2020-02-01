import socket
import time


class HMP4040(object):
    def __init__(self, ip='192.168.101.4', port="5025"):
        self.Debug = True
        self.IP = ip
        self.Port = port
        self.client = socket.socket()
        self.connectionStatus = False
        #if self.connect(ip, port):
            #self.connectionStatus = True
        #else:
            #self.connectionStatus = False
            
    def __str__(self):

        return "LBS HMP4040 connection = " + str(self.connectionStatus) + \
               "\nIP: %s" % self.IP + "\nPort: " + str(self.Port)

    def __repr__(self):
        return str(self)

    def get_ip(self):
        return self.IP

    def get_port(self):
        return self.Port

    def connect(self, ip='10.6.1.4', port="5025"):
        """
        Устанавливает соединение с ЛБП
        :param ip: адрес ЛБП
        :param port: порт ЛБП
        :return: При успешном подключении возвращает истину, иначе ложь
        """
        self.IP = ip
        self.Port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(1)
        self._myprint("trying to connect to " + str(ip) + " : %d" % int(port))
        try:
            self.client.connect((ip, int(port)))
        except socket.error as exc:
            self._myprint('Caught exception socket.error : %s' % exc)
            self.connectionStatus = False
            return False
        else:
            self._myprint('connected to server ' + ip + ':' + str(port))
            self.connectionStatus = True
            return True

    def reconnect(self):
        self.disconnect()
        return self.connect(self.get_ip(), self.get_port())

    def disconnect(self):
        self.client.close()
        self.connectionStatus = False
        self._myprint('disconnected')

    def _myprint(self, text):
        if self.Debug:
            print(text)

    def __check_voltage(self, voltage="1.0"):
        """
        Проверяет указанное напряжение на допустимость для данного блока питания
        :param voltage: напряжение на канал
        :return: При корректно указанном напряжении возвращает истину, иначе ложь

        """

        try:
            float(voltage)
            if (float(voltage) >= 0) and (float(voltage) <= 30):
                return True
            else:
                return False
        except ValueError:
            return False

    def __check_current(self, current="0.1"):
        """
        Проверяет указанную величину тока на допустимость для данного блока питания
        :param current: ток на канал
        :return: При корректно указанном токе возвращает истину, иначе ложь
        """
        
        try:
            float(current)
            if (float(current) >= 0) and (float(current) <= 10):
                return True
            else:
                return False
        except ValueError:
            return False

    def __check_channel(self, channels_=('1', '2', '3', '4')):
        """
        Проверяет передаваемый кортеж на наличие недопустимых значений и соответствие одному из четырех каналов
        :param channels_: передаваемый кортеж с номерами каналов
        :return: в случае ошибки возвращает ложь; в случае успеха истину
        """
        for i in channels_:
            try:
                int(i)
                if not((int(i) >= 1) and (int(i) <= 4)):
                    return False
            except ValueError:
                return False
        return True

    def __check_fuse_delay(self, delay=50):
        try:
            int(delay)
            if (delay < 0) and (delay > 250):
                return False
        except ValueError:
            return False
        return True

    def __for_each_channel(self, *__check_functions, ch=('1', '2', '3', '4'), cmd=''):
        """
        Универсальная функция служит для уменьшения количества кода. Производит проверку входящих данных на валидность и
        в случае некорректных данных возвращает ложь. Если все данные корректны, то проверяет тип отправляемой команды.
        Обычная команда возвращает истину, а команда запроса возвращает список данных со всех указанных каналов.
        :param __check_functions: список функций проверки входящих данных
        :param ch: список каналов
        :param cmd: команда, отправляемая на выбранные каналы
        :return: В случае корректных входных данных возвращает истину, иначе ложь. Если команда запроса данных, то
        взвращает список полученных данных

        """
        # Блок проверки входящих данных (начало)
        for func in __check_functions:
            if func:
                continue
            else:
                return False
        # Блок проверки входящих данных (конец)

        # Проверка типа команды. Для запроса данных возвращает список. Для обычной команды при корректных входных
        # возвращает истину.
        if cmd.find('?') != -1:
            received_data = []
            for i in ch:
                self.send_command("INST OUT" + str(i))
                received_data.append(self.send_command(cmd))
            return received_data
        elif cmd == '':
            return False
        else:
            for i in ch:
                self.send_command('INST OUT' + str(i))
                self.send_command(cmd)
            return True

    def send_command(self, cmd):
        """
        Отправляет команду на ЛБП. Если подразумевается, что должен придти ответ, то исполнение программы
        приостанавливается до тех пор, пока ответ не будет получен.
        :param cmd: Команда для отправки в ЛБП
        :return: Если ожидается ответ, то возвращается строка с ответом, иначе ничего не возвращает

        """
        self._myprint('client send: ' + cmd)
        if cmd.find('?') != -1:
            self.client.send((cmd + '\n').encode())
            received_data = self.client.recv(1024).decode()
            self._myprint("received: " + received_data)
            return received_data
        else:
            self.client.send((cmd + '\n').encode())
            time.sleep(0.05)
            return None

    def set_voltage(self, channels_=('1', '2', '3', '4'), voltage="0.0"):
        """
        Устанавливает указанное напряжение на выбранных каналах
        :param channels_: кортеж выбранных каналов
        :param voltage: уровень напряжения для выбранных каналов
        :return: При отсутствии ошибок возвращает истину. При указании недопустимого канала возвращает ложь
        """
        return self.__for_each_channel((self.__check_channel(channels_), self.__check_voltage(voltage)),
                                       ch=channels_, cmd="VOLT " + str(voltage))

    def get_voltage(self, channels_=('1', '2', '3', '4')):
        """
        Запрашивает у ЛБП текущие параметры напряжения на указанных каналах
        :param channels_: список каналов на которых нужно измерить текущее напряжение
        :return: В случае корректных аргументов возвращает кортеж значений напряжений для каждого указанного канала,
        иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd="VOLT?")
            
    def set_current(self, channels_=('1', '2', '3', '4'), current="0.1"):
        """
        Задает ток на выбранных каналах
        :param channels_: список каналов, ка которых будет выставлено новое значение тока
        :param current: величина тока
        :return: истина при вводе корректных данных, иначе ложь
        """
        return self.__for_each_channel((self.__check_channel(channels_), self.__check_current(current)),
                                       ch=channels_, cmd="CURR " + str(current))

    def get_current(self, channels_=('1', '2', '3', '4')):
        """
        Запрашивает текущий ток на выбранных каналах
        :param channels_: список каналов
        :return: В случае корректных аргументов возвращает кортеж значений тока для каждого указанного канала,
        иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd="CURR?")

    def get_status_byte(self):
        return self.send_command('*STB?')

    def get_event_status(self):
        return self.send_command('*ESR?')

    def check_sound(self):
        self.send_command('SYST:BEEP')

    def get_version(self):
        """
        :return: возвращает номер версии SCPI
        """
        return self.send_command('SYST:VERS?')

    def get_errors(self):
        """
        :return: возврощает код ошибки 0 - нет ошибок; -100 - ошибка команды;
                 -102 - синтаксическая ошибка; -350 - переполнение очереди
        """
        return self.send_command('SYST:ERR?')

    def get_identification_info(self):
        """
        :return: возвращает тип устройства, серийный номер и номер прошивки
        """
        return self.send_command('*IDN?')

    def get_last_channel(self):
        """
        :return: возвращает номер активного канала в виде строки "OUTx", где х - номер канала
        """
        return self.send_command('INST?')

    def set_step_voltage(self, step_="1.0"):  # Переделать для списка каналов
        """
        Устанавливает величину шага напряжения. Начальное значение 1.000. Допустимые значения от 0.000 до 32.050
        :param step_: шаг напряжения
        :return: При корректных аргументах возвращает истину, иначе ложь
        """
        if self.__check_voltage(step_):
            self.send_command('VOLT:STEP ' + str(step_))
            return True
        else:
            return False

    def get_step_voltage(self):
        """
        :return: Возвращает величину шага напряжения.
        """
        return self.send_command('VOLT:STEP?')

    def voltage_up(self, channels_=('1', '2', '3', '4')):
        """
        Увеличивает напряжение на выбранных каналах на величину, указанную в предыдущей коменде
        или на дефолтное значение
        :param channels_: каналы, на которых будет изменять напряжение
        :return: Возвращает истину при корректных аргументах, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='VOLT UP')

    def voltage_down(self, channels_=('1', '2', '3', '4')):
        """
        Уменьшает напряжение на выбранных каналах на величину, установленную командой set_step_current(current)
        :param channels_: Каналы, на которых уменьшится напряжение
        :return: Возвращает истину при корректных аргументах, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='VOLT DOWN')

    def set_step_current(self, step="0.1"):
        """
        Проверяет указанное значение шага величины тока, чтобы оно не выходило за допустимый диапазон. Если значение
        лежит в допустимом интервале, то устанавливает указанное значение. В противном случае, возвращает ложь.
        :param step: значение шага тока.
        :return: При корректных аргументах возвращает истину, иначе ложь.
        """
        if self.__check_current(step):
            self.send_command('CURR:STEP ' + str(step))
            return True
        else:
            return False

    def get_step_current(self):
        """
        :return: Возвращает текущее значение шага тока
        """
        return self.send_command('CURR:STEP?')

    def current_up(self, channels_=('1', '2', '3', '4')):
        """
        Увеличивает величину тока тока на выбранных каналах
        :return: В случае корректных аргументов возвращает истину, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='CURR UP')

    def current_down(self, channels_=('1', '2', '3', '4')):
        """
        Уменьшает величину тока на выбранных каналах
        :param channels_: список каналов
        :return: В случае корректных аргументов возвращает истину, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='CURR DOWN')

    def set_channel_params(self, channels_=('1', '2', '3', '4'), voltage="1.0", current="1.0"):
        """
        Устанавливает на выбранном списке каналов указанные значения тока и напряжения
        :param channels_: список каналов
        :param voltage: напряжение
        :param current: ток
        :return: В случае корректных аргументов возвращает истину, иначе ложь

        """
        return self.__for_each_channel(
            (self.__check_channel(channels_), self.__check_voltage(voltage), self.__check_current(current)),
            ch=channels_, cmd='APPL ' + str(voltage) + ',' + str(current))

    def get_channel_params(self, channels_=('1', '2', '3', '4')):
        """
        Возвращает текущие значения напряжения и тока для списка выбранных каналов
        :param channels_: список каналов
        :return: В случае корректных аргументов возвращает список, содержащий данные напряжения и тока
        для каждого указанного канала, иначе возвращает ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='APPL?')

    def is_output_turned_on(self):
        return self.send_command('OUTP:GEN?')

    def turn_on_selected_channels(self):
        """
        Коммутирует выбранные каналы на физический выход ЛБП
        :return: True
        """
        return self.send_command('OUTP:GEN 1')

    def turn_off_selected_channels(self):
        """
        Отлючает от физического выхода ЛБП все каналы
        :return: True
        """
        return self.send_command('OUTP:GEN 0')

    def select_on_channel(self, channels_=('1', '2', '3', '4')):
        """
        Включает выбранные каналы
        :param channels_: список каналов
        :return: В случае корректных аргументов возвращает истину, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='OUTP:SEL 1')

    def select_off_channel(self, channels_=('1', '2', '3', '4')):
        """
        Выключает выбранные каналы
        :param channels_: список каналов
        :return: В случае корректных аргументов возвращает истину, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='OUTP:SEL 0')

    def get_active_channel(self, channels_=('1', '2', '3', '4')):
        """
        Возвращает список элементов, где 1 - канал включен, 0 - выключен
        :param channels_: список каналов
        :return: В случае корректных аргументов возвращает истину, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), cmd='OUTP?')

    def set_overvoltage_protection_value(self, channels_=('1', '2', '3', '4'), max_voltage="10.0"):
        """
        Устанавливает уровень срабатывания защиты от перенапряжения для каждого канала из списка
        :param channels_:  список каналов
        :param max_voltage: уровень срабатывания предохранителя
        :return: В случае корректных аргументов возвращает истину, иначе ложь
        """
        return self.__for_each_channel((self.__check_channel(channels_), self.__check_voltage(max_voltage)),
                                       ch=channels_, cmd='VOLT:PROT ' + str(max_voltage))

    def get_overvoltage_protection_value(self, channels_=('1', '2', '3', '4')):
        """
        :param channels_: список каналов
        :return: Возвращает список значений уровня срабатывания защиты по напряжению для каждого канала
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='VOLT:PROT?')

    def clear_overvoltage_protection(self, channels_=('1', '2', '3', '4')):
        """
        Бесполезная функция, которая просто убирает мигающую надпись "ovp". Для отключения защиты достаточно просто
        снизить напряжение до допустимого значения и снова скоммутировать отключенные выход ЛБП
        :param channels_: список каналов
        :return: В случае корректных аргументов возвращает список, хранящий значения состояния каналов. Иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='VOLT:PROT:CLE')

    def get_overvoltage_channels_tripped(self, channels_=('1', '2', '3', '4')):
        """
        Проверяет состояние переданных каналов на факт срабатывание защиты от перенапряжения
        :param channels_: список каналов
        :return: При корректных данных возвращает список, содержащий состояния защиты от перенапряжения каналов.
        """
        tripped_channels = []
        if self.__check_channel(channels_):
            for i in channels_:
                self.send_command('INST OUT' + str(i))
                if int(self.send_command('VOLT:PROT:TRIP?')):
                    tripped_channels.append(i)
            return tripped_channels
        else:
            return False

    def is_overvoltege_channel_tripped(self, channels_=('1', '2', '3', '4')):
        """
        Проверяет состояние переданных каналов на факт срабатывание защиты от перенапряжения
        :param channels_: список каналов
        :return: При корректных данных возвращает список, содержащий состояния защиты от перенапряжения каналов.
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='VOLT:PROT:TRIP?')

    def meas_overvoltage_protection(self, channels_=('1', '2', '3', '4')):
        """
        Включает защиту от перенапряжения в режиме MEAS. После указанаия уровня срабатывания ниже максимального
        значения и включения защиты канала, при превышении напряжения на канале будет всегда срабатывать защита,
        отключая тем самым канал от выхода. Для предотвращения срабатывания необходимо сначала увеличить порог
        срабатывания.
        :param channels_: список каналов
        :return: При корректных данных возвращает список, содержащий состояния защиты от перенапряжения каналов.
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='VOLT:PROT:MODE MEAS')

    def is_overvoltage_protection_active(self, channels_=('1', '2', '3', '4')):
        """
        :param channels_: список каналов
        :return: Возвращает режим работы предохранителя для указанных каналов
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='VOLT:PROT:MODE MEAS?')

    def measure_voltage(self, channels_=('1', '2', '3', '4')):
        """
        Внутреннее измеренеие напряжения?
        :param channels_: список каналов
        :return: список напряжений на каждом канале
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='MEAS:VOLT?')

    def reset_hmp4040(self):
        return self.send_command("*RST")

    def measure_current(self, channels_=('1', '2', '3', '4')):
        """
        Внутреннее измерение тока?
        :param channels_: список каналов
        :return: список значений токов на каждом канале
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='MEAS:CURR?')

    def set_fuse_delay(self, channels_=('1', '2', '3', '4'), delay_=10):
        """
        Устанавливает время задержки срабатывания предохранителя по току
        :param channels_: список каналов, для которых будет применяться данная функция
        :param delay_: время задержки в миллисекундах
        :return: При корректных данных возвращает список, содержащий состояния защиты от перенапряжения каналов.
        """
        return self.__for_each_channel((self.__check_channel(channels_), self.__check_fuse_delay(delay_)),
                                       ch=channels_, cmd='FUSE:DEL ' + str(delay_))

    def get_fuse_delay(self, channels_=('1', '2', '3', '4')):
        """
        :param channels_: список каналов
        :return: Возвращает список, содержащий время задержки для каждого из указанных каналов
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='FUSE:DEL?')

    def set_link_fuse(self, source_channel, channels_=('1', '2', '3', '4')):
        """
        Связывает уазанный канал со всеми каналами из списка, тем самым при срабатывании защиты на канале, от выхода
        также отключатся и связанные каналы.
        :param source_channel: номер канала, с которым связывают каналы из списка
        :param channels_: список каналов, которые связывают с каналом-источником
        :return: При корректных данных возвращает список, содержащий состояния защиты от перенапряжения каналов.
        """
        if self.__check_channel([source_channel]) and self.__check_channel(channels_):
            self.send_command('INST OUT' + str(source_channel))
            for i in channels_:
                if source_channel != i:
                    self.send_command('FUSE:LINK ' + str(i))
            return True
        else:
            return False

    def get_link_fuse(self, source_channel, channels_=('1', '2', '3', '4')):
        """
        :param source_channel: канал-источник
        :param channels_: список каналов
        :return: Взвращает список привязанных каналов к каналу-источнику. Если входные данные некорректны, то ложь
        """
        if self.__check_channel([source_channel]) and self.__check_channel(channels_):
            self.send_command('INST OUT' + str(source_channel))
            linked_chennels = []
            for i in channels_:
                if source_channel != i:
                    linked_chennels.append(self.send_command('FUSE:LINK? ' + str(i)))
            return linked_chennels
        else:
            return False

    def unlink_fuse(self, source_channel, channels_=('1', '2', '3', '4')):
        """
        Отвязывает от канала источника те каналы, которые указаны в списке
        :param source_channel: канал-источник
        :param channels_: список каналов
        :return: При корректных данных возвращает истину, иначе ложь
        """
        if self.__check_channel([source_channel]) and self.__check_channel(channels_):
            self.send_command('INST OUT' + str(source_channel))
            for i in channels_:
                if source_channel != i:
                    self.send_command('FUSE:UNL ' + str(i))
            return True
        else:
            return False

    def get_fuse_channels_tripped(self, channels_=('1', '2', '3', '4')):
        """
        Проверяет состояние переданных каналов на факт срабатывание защиты по току
        :param channels_: список каналов
        :return: При корректных данных возвращает список, содержащий состояния защиты по току каналов.
        """
        tripped_channels = []
        if self.__check_channel(channels_):
            for i in channels_:
                self.send_command('INST OUT' + str(i))
                if int(self.send_command('FUSE:TRIP?')):
                    tripped_channels.append(i)
            return tripped_channels
        else:
            return False

    def set_on_fuse_channels(self, channels_=('1', '2', '3', '4')):
        """
        Включает предохранители на выбранных каналах
        :param channels_: список каналов
        :return: При корректных данных возвращает истину, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='FUSE 1')

    def set_off_fuse_channels(self, channels_=('1', '2', '3', '4')):
        """
        Выключает предохранители на выбранных каналах
        :param channels_: список каналов
        :return: При корректных данных возвращает истину, иначе ложь
        """
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='FUSE 0')

    def clear_arbitrary_data(self, channels_=('1', '2', '3', '4')):
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='ARB:CLEAR 1')

    def set_arbitrary_sequence(self, channels_=('1', '2', '3', '4'), sequence=""):
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='ARB:DATA ' + str(sequence))

    def set_arbitrary_sequence_repeat(self, channels_=('1', '2', '3', '4'), repeat="1"):
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='ARB:REP ' + str(repeat))

    def start_arbitrary_sequence(self, channels_=('1', '2', '3', '4')):
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='ARB:STAR 1')

    def stop_arbitrary_sequence(self, channels_=('1', '2', '3', '4')):
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='ARB:STOP 1')

    def transfer_arbitrary(self, channels_=('1', '2', '3', '4')):
        return self.__for_each_channel(self.__check_channel(channels_), ch=channels_, cmd='ARB:TRAN 1')

if __name__ == "__main__":
    LBS = HMP4040()
    print(LBS)
    if LBS.connect(ip="10.6.1.4", port='5025'):
        #LBS.check_sound()
        LBS.get_version()
        print(LBS.get_identification_info())
        LBS.get_errors()
        print(LBS.get_status_byte())

        channels = ['1', '2', '3', '4']
        # LBS.set_voltage(channels, 3.1)
       #  LBS.set_current(channels, 1.5)
       #  LBS.turn_off_selected_channels()
       #  LBS.select_off_channel(channels)
        # LBS.select_on_channel(channels)
        # LBS.turn_on_selected_channels()
        # print(LBS.set_overvoltage_protection_value(['1', '2', '3'], 5.1))
        # LBS.meas_overvoltage_protection(['1'])
        # LBS.set_voltage(['1', '3'], 5.3)
       #  LBS.is_overvoltage_protection_active(['1'])
       #  print(LBS.get_overvoltage_channels_tripped(channels))
        # LBS.clear_overvoltage_protection(channels)
        # LBS.voltage_up(channels)
        # LBS.set_on_fuse_channels(channels)
        # LBS.set_link_fuse(1, channels)
        # LBS.set_link_fuse(2, ['3', '4'])
        # print(LBS.get_link_fuse(1))
        # print(LBS.get_link_fuse(2))
        # LBS.set_off_fuse_channels(channels)
        # print(LBS.get_active_channel(channels))
        # LBS.currentDown()
        while True:
            req = input('enter some text: ')
            if req == 'exit':
                break
            LBS.send_command(req)
        LBS.disconnect()
