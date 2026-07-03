// Copyright (c) 2020 madVR Labs, LLC. All rights reserved.

// Permission is hereby granted to use this sample and make
// derivative works therefore, for use in conjunction with
// the madVR Envy hardware and software.

unit EnvyIpControlMainForm;

interface

uses
  Windows, Messages, SysUtils, Variants, Classes, Graphics, Controls, Forms,
  Dialogs, StdCtrls, ExtCtrls;

type
  TFileType = (ft3dlut, ftSettings, ftEdid);

type
  TFEnvyIpControlMainForm = class(TForm)
    LogMemo: TMemo;
    HeartbeatTimer: TTimer;
    GroupBox1: TGroupBox;
    IpAddrEdit: TEdit;
    ConnectButton: TButton;
    DisconnectButton: TButton;
    GroupBox2: TGroupBox;
    GroupBox3: TGroupBox;
    MacAddrEdit: TEdit;
    WakeButton: TButton;
    CommandEdit: TEdit;
    SendCommandButton: TButton;
    GroupBox4: TGroupBox;
    PowerOffButton: TButton;
    StandbyButton: TButton;
    RestartButton: TButton;
    GroupBox5: TGroupBox;
    IncomingSignalButton: TButton;
    OutgoingSignalButton: TButton;
    AspectRatioButton: TButton;
    TemperaturesButton: TButton;
    GroupBox6: TGroupBox;
    StoreInstallerButton: TButton;
    RestoreInstallerButton: TButton;
    GroupBox7: TGroupBox;
    StoreSuggestedButton: TButton;
    RestoreSuggestedButton: TButton;
    GroupBox8: TGroupBox;
    StoreUserSlotButton: TButton;
    RestoreUserSlotButton: TButton;
    GroupBox9: TGroupBox;
    DownloadSettingsButton: TButton;
    UploadSettingsButton: TButton;
    GroupBox10: TGroupBox;
    EnumLutButton: TButton;
    RenameLutButton: TButton;
    DeleteLutButton: TButton;
    DownloadLutButton: TButton;
    UploadLutButton: TButton;
    GroupBox11: TGroupBox;
    DownloadCurrentEdidButton: TButton;
    UploadEdidButton: TButton;
    DownloadEdidSlotButton: TButton;
    SaveDialog: TSaveDialog;
    OpenDialog: TOpenDialog;
    RemoteBmp: TImage;
    ButtonDownTimer: TTimer;
    procedure FormCreate(Sender: TObject);
    procedure FormKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
    procedure CommandEditKeyPress(Sender: TObject; var Key: Char);
    procedure HeartbeatTimerTimer(Sender: TObject);
    procedure UpdateControls(Sender: TObject);
    procedure ConnectButtonClick(Sender: TObject);
    procedure DisconnectButtonClick(Sender: TObject);
    procedure SendCommandButtonClick(Sender: TObject);
    procedure WakeButtonClick(Sender: TObject);
    procedure PowerOffButtonClick(Sender: TObject);
    procedure StandbyButtonClick(Sender: TObject);
    procedure RestartButtonClick(Sender: TObject);
    procedure IncomingSignalButtonClick(Sender: TObject);
    procedure OutgoingSignalButtonClick(Sender: TObject);
    procedure AspectRatioButtonClick(Sender: TObject);
    procedure TemperaturesButtonClick(Sender: TObject);
    procedure StoreInstallerButtonClick(Sender: TObject);
    procedure RestoreInstallerButtonClick(Sender: TObject);
    procedure StoreSuggestedButtonClick(Sender: TObject);
    procedure RestoreSuggestedButtonClick(Sender: TObject);
    procedure StoreUserSlotButtonClick(Sender: TObject);
    procedure RestoreUserSlotButtonClick(Sender: TObject);
    procedure DownloadSettingsButtonClick(Sender: TObject);
    procedure UploadSettingsButtonClick(Sender: TObject);
    procedure EnumLutButtonClick(Sender: TObject);
    procedure RenameLutButtonClick(Sender: TObject);
    procedure DeleteLutButtonClick(Sender: TObject);
    procedure DownloadLutButtonClick(Sender: TObject);
    procedure UploadLutButtonClick(Sender: TObject);
    procedure DownloadCurrentEdidButtonClick(Sender: TObject);
    procedure DownloadEdidSlotButtonClick(Sender: TObject);
    procedure UploadEdidButtonClick(Sender: TObject);
    procedure RemoteBmpMouseDown(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
    procedure RemoteBmpMouseUp(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
    procedure ButtonDownTimerTimer(Sender: TObject);
  private
    { Private declarations }

    // socket handling stuff
    FSocket : THandle;
    FRemains : AnsiString;

    // file download stuff
    FFileBuf : PAnsiChar;
    FFileLen : integer;
    FFilePos : integer;
    FFileCrc : dword;
    FFileFile : UnicodeString;
    FFileSlot : integer;
    FFileType : TFileType;
    FFileTick : dword;

    // 3dlut enumeration
    FLutFiles : UnicodeString;
    FLutFilesTemp : UnicodeString;

    // keep log clean
    FIgnoreOk : boolean;
    FIgnoreMac : boolean;
    FIgnore3dlut : boolean;

    // remote control button handling
    FButtonDown : AnsiString;

    // socket handling stuff
    procedure SocketReadThread;
    procedure HandleReceivedData(var Message: TMessage); message WM_USER + 777;
    procedure HandleConnectionClose(var Message: TMessage); message WM_USER + 778;
    function HandleFileDownload(buf: PAnsiChar; len: integer) : integer;

    // various helper functions
    function DoOpenDialog(title, filters: string; allowMultiSelect: boolean) : string;
    function DoSaveDialog(title, filters, fileName: string) : string;
    function PrepareUpload(const fileName: UnicodeString; out crc: dword; out data: AnsiString) : boolean;
    function Enum3dlutFiles : boolean;
  end;

var
  FEnvyIpControlMainForm: TFEnvyIpControlMainForm;

implementation

{$R *.dfm}

uses EnvyIpControlSlotBox, WinSock, madStrings, madTools, madTypes, madCrypt, madZip, Math, ShlObj;

// registry functions ---------------------------------------------------------

function Reg_GetString(key: HKEY; const path: UnicodeString; name: PWideChar; out value: UnicodeString) : boolean;
var hk1  : HKEY;
    size : dword;
begin
  result := false;
  value := '';
  if RegOpenKeyExW(key, PWideChar(path), 0, KEY_QUERY_VALUE, hk1) = 0 then begin
    size := MAX_PATH;
    if RegQueryValueExW(hk1, name, nil, nil, nil, @size) = 0 then begin
      SetLength(value, size);
      result := (size = 0) or (RegQueryValueExW(hk1, name, nil, nil, pointer(PWideChar(value)), @size) = 0);
      if result then
        value := PWideChar(value)
      else
        value := '';
    end;
    RegCloseKey(hk1);
  end;
end;

function Reg_SetString(key: HKEY; const path: UnicodeString; name: PWideChar; const value: UnicodeString) : boolean;
var hk1 : HKEY;
begin
  result := false;
  if RegCreateKeyExW(key, PWideChar(path), 0, nil, 0, KEY_ALL_ACCESS, nil, hk1, nil) = 0 then begin
    result := RegSetValueExW(hk1, name, 0, REG_SZ, PWideChar(value), Length(value) * 2 + 2) = 0;
    RegCloseKey(hk1);
  end;
end;

// low level socket functions -------------------------------------------------

function SocketCreate(const ip: AnsiString; port: dword) : THandle;
var sin : sockaddr_in;
    fds : TFDSet;
    tv  : TTimeVal;
    i1  : integer;
    b1  : boolean;
begin
  result := socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
  if result <> THandle(INVALID_SOCKET) then begin
    sin.sin_family := AF_INET;
    sin.sin_addr.s_addr := inet_addr(PAnsiChar(ip));
    sin.sin_port := htons(port);
    i1 := 1;
    ioctlsocket(result, FIONBIO, i1);
    connect(result, sin, sizeof(sin));
    // time out after 2 seconds
    tv.tv_sec := 2;
    tv.tv_usec := 0;
    fds.fd_count := 1;
    fds.fd_array[0] := result;
    b1 := select(0, nil, @fds, nil, @tv) > 0;
    i1 := 0;
    ioctlsocket(result, FIONBIO, i1);
    if not b1 then begin
      closesocket(result);
      result := 0;
    end;
  end;
end;

function SocketSend(socket: THandle; sendBuf: AnsiString) : boolean;
begin
  result := send(socket, sendBuf[1], Length(sendBuf), 0) <> SOCKET_ERROR;
end;

function SocketReceive(socket: THandle; timeOut: integer = 5) : AnsiString;
var buf  : array [0..1023] of byte;
    size : integer;
    fds  : TFDSet;
    tv   : TTimeVal;
begin
  result := '';
  fds.fd_count := 1;
  fds.fd_array[0] := socket;
  tv.tv_sec := timeOut;
  tv.tv_usec := 0;
  if select(0, @fds, nil, nil, @tv) <= 0 then
    exit;
  size := recv(socket, buf, sizeOf(buf), 0);
  if size <= 0 then
    exit;
  SetLength(result, size);
  if size > 0 then
    Move(buf[0], pointer(result)^, size);
end;

procedure SocketClose(socket: THandle);
var ling : TLinger;
begin
  shutdown(socket, SD_SEND);
  repeat until SocketReceive(socket, 1) = '';
  ling.l_onoff := 1;
  ling.l_linger := 0;
  setsockopt(socket, SOL_SOCKET, SO_LINGER, @ling, sizeOf(ling));
  closesocket(socket);
end;

function WakeOnLAN(const ip, mac: AnsiString) : boolean;
var socketHandle : TSocket;
    sin          : sockaddr_in;
    option       : integer;
    packet       : array [0..101] of byte;
    i1, i2       : integer;
begin
  result := false;
  socketHandle := socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
  if socketHandle <> INVALID_SOCKET then begin
    option := 1;
    if setsockopt(socketHandle, SOL_SOCKET, SO_BROADCAST, @option, sizeof(option)) = 0 then begin
      for i1 := 0 to 5 do
        packet[i1] := $ff;
      for i1 := 1 to 16 do
        for i2 := 0 to 5 do
          packet[i1 * 6 + i2] := ord(mac[i2 + 1]);
      sin.sin_family := AF_INET;
      sin.sin_port := htons(9);
      sin.sin_addr.s_addr := inet_addr(PAnsiChar(SubStr(ip, 1, '.') + '.' + SubStr(ip, 2, '.') + '.' + SubStr(ip, 3, '.') + '.255'));
      result := sendto(socketHandle, packet, sizeof(packet), 0, sin, sizeof(sin)) = sizeOf(packet);
      sin.sin_addr.s_addr := inet_addr(PAnsiChar(SubStr(ip, 1, '.') + '.' + SubStr(ip, 2, '.') + '.255.255'));
      sendto(socketHandle, packet, sizeof(packet), 0, sin, sizeof(sin));
      sin.sin_addr.s_addr := inet_addr(PAnsiChar(SubStr(ip, 1, '.') + '.255.255.255'));
      sendto(socketHandle, packet, sizeof(packet), 0, sin, sizeof(sin));
    end;
    closesocket(socketHandle);
  end;
end;

// socket handling stuff ------------------------------------------------------

function SocketReadThreadProc(self: TFEnvyIpControlMainForm) : dword; stdcall;
begin
  self.SocketReadThread;
  result := 0;
end;

procedure TFEnvyIpControlMainForm.SocketReadThread;
var buf : pointer;
    len : integer;
begin
  buf := VirtualAlloc(nil, 1024 * 1024, MEM_COMMIT, PAGE_READWRITE);
  while true do begin
    len := recv(FSocket, buf^, 1024 * 1024, 0);
    if len <= 0 then
      break;
    SendMessage(Handle, WM_USER + 777, NativeInt(buf), len);
  end;
  VirtualFree(buf, 0, MEM_RELEASE);
  // notify main thread that the connection went down
  SendMessage(Handle, WM_USER + 778, 0, 0);
end;

procedure TFEnvyIpControlMainForm.HandleReceivedData(var Message: TMessage);
var s1, s2     : AnsiString;
    us1        : UnicodeString;
    i1, i2, i3 : integer;
    buf        : PAnsiChar;
    len, len2  : integer;
begin
  // this runs in the context of the main thread
  buf := pointer(Message.wParam);
  len := Message.lParam;
  len2 := HandleFileDownload(buf, len);
  inc(buf, len2);
  dec(len, len2);
  if len > 0 then begin
    SetString(s1, buf, len);
    ReplaceStrA(s1, #$d#$a, #$a);
    s1 := FRemains + s1;
    for i1 := 1 to SubStrCountA(s1, #$a) - 1 do begin
      s2 := SubStrA(s1, i1, #$a);
      len2 := HandleFileDownload(pointer(s2), Length(s2));
      if len2 > 0 then
        Delete(s2, 1, len2);
      if s2 <> '' then
        if (FIgnoreOk or FIgnore3dlut or FIgnoreMac) and (s2 = 'OK') then
          FIgnoreOk := false
        else
          if ((FButtonDown <> 'LEFT') and (FButtonDown <> 'RIGHT') and (FButtonDown <> 'UP') and (FButtonDown <> 'DOWN')) or (ButtonDownTimer.Interval = 600) or (s2 <> 'KeyPress ' + FButtonDown) then
            if PosTextIs1A('MacAddress ', s2) then begin
              // whenever the MacAddress is reported, we store it in the registry
              if FIgnoreMac then
                FIgnoreMac := false
              else
                LogMemo.Lines.Add(DecodeUtf8(s2));
              MacAddrEdit.Text := UnicodeString(Copy(s2, 12, maxInt));
              Reg_SetString(HKEY_CURRENT_USER, 'Software\madshi\madVR', 'EnvyIpControl - MacAddr', MacAddrEdit.Text);
            end else
              if PosTextIs1A('3DLUTFile', s2) then begin
                // when Envy enumerates the 3DLUT files, we store the info internally
                if not FIgnore3dlut then
                  LogMemo.Lines.Add(DecodeUtf8(s2));
                if PosTextIs1A('3DLUTFile.', s2) then begin
                  // enumeration is now complete
                  FLutFiles := FLutFilesTemp;
                  FLutFilesTemp := '';
                  FIgnore3dlut := false;
                end else begin
                  us1 := DecodeUtf8(Copy(s2, 11, maxInt));
                  TrimStrW(us1);
                  if (us1 <> '') and (us1[1] = '"') then
                    Delete(us1, 1, 1);
                  if (us1 <> '') and (us1[Length(us1)] = '"') then
                    DeleteRW(us1, 1);
                  if FLutFilesTemp <> '' then
                    FLutFilesTemp := FLutFilesTemp + '|';
                  FLutFilesTemp := FLutFilesTemp + us1;
                end;
              end else begin
                LogMemo.Lines.Add(DecodeUtf8(s2));
                if PosTextIs1A('Download3DLUTFile ', s2) then begin
                  // Envy is sending us a 3DLUT file
                  FFileType := ft3dlut;
                  FFileLen := StrToIntDef(UnicodeString(SubStrA(s2, 2, ' ')), 0);
                  FFileBuf := VirtualAlloc(nil, FFileLen, MEM_COMMIT, PAGE_READWRITE);
                  FFilePos := 0;
                  FFileCrc := StrToIntDef('$' + UnicodeString(SubStrA(s2, 3, ' ')), 0);
                  if (FFileFile <> '') and ((ExtractFileExt(FFileFile) <> '.3dlut') or (GetTickCount - FFileTick > 10000)) then
                    FFileFile := '';
                  if FFileFile = '' then begin
                    i3 := 0;
                    for i2 := 1 to Length(s2) do
                      if s2[i2] = ' ' then begin
                        inc(i3);
                        if i3 = 3 then begin
                          FFileFile := DecodeUtf8(Copy(s2, i2 + 1, maxInt));
                          TrimStrW(FFileFile);
                          break;
                        end;
                      end;
                    if (FFileFile <> '') and (FFileFile[1] = '"') then
                      Delete(FFileFile, 1, 1);
                    if (FFileFile <> '') and (FFileFile[Length(FFileFile)] = '"') then
                      DeleteRW(FFileFile, 1);
                    if FFileFile = '' then
                      FFileFile := 'Downloaded.3dlut';
                  end;
                end else
                  if PosTextIs1A('DownloadSettingsFile ', s2) then begin
                    // Envy is sending us a Settings file
                    FFileType := ftSettings;
                    FFileLen := StrToIntDef(UnicodeString(SubStrA(s2, 2, ' ')), 0);
                    FFileBuf := VirtualAlloc(nil, FFileLen, MEM_COMMIT, PAGE_READWRITE);
                    FFilePos := 0;
                    FFileCrc := StrToIntDef('$' + UnicodeString(SubStrA(s2, 3, ' ')), 0);
                    if (FFileFile <> '') and ((ExtractFileExt(FFileFile) <> '.envy') or (GetTickCount - FFileTick > 10000)) then
                      FFileFile := '';
                    if FFileFile = '' then
                      FFileFile := 'Settings.envy';
                  end else
                    if PosTextIs1A('DownloadEDIDFile ', s2) then begin
                      // Envy is sending us an EDID block
                      FFileType := ftEdid;
                      FFileLen := StrToIntDef(UnicodeString(SubStrA(s2, 2, ' ')), 0);
                      FFileBuf := VirtualAlloc(nil, FFileLen, MEM_COMMIT, PAGE_READWRITE);
                      FFilePos := 0;
                      FFileCrc := StrToIntDef('$' + UnicodeString(SubStrA(s2, 3, ' ')), 0);
                      if (FFileFile <> '') and ((ExtractFileExt(FFileFile) <> '.edid') or (GetTickCount - FFileTick > 10000)) then
                        FFileFile := '';
                      if FFileFile = '' then begin
                        FFileFile := '';
                        i3 := 0;
                        for i2 := 1 to Length(s2) do
                          if s2[i2] = ' ' then begin
                            inc(i3);
                            if i3 = 3 then begin
                              FFileFile := DecodeUtf8(Copy(s2, i2 + 1, maxInt));
                              TrimStrW(FFileFile);
                              break;
                            end;
                          end;
                        if (FFileFile <> '') and (FFileFile[1] = '"') then
                          Delete(FFileFile, 1, 1);
                        if (FFileFile <> '') and (FFileFile[Length(FFileFile)] = '"') then
                          DeleteRW(FFileFile, 1);
                        if FFileFile = '' then
                          FFileFile := 'Downloaded';
                        FFileFile := FFileFile + '.edid';
                      end;
                    end;
              end;
    end;
    FRemains := SubStrA(s1, SubStrCountA(s1, #$a), #$a);
    if (FRemains <> '') and (FFileBuf <> nil) and (FFilePos + Length(FRemains) <= FFileLen) then begin
      Move(pointer(FRemains)^, FFileBuf[FFilePos], Length(FRemains));
      inc(FFilePos, Length(FRemains));
      FRemains := '';
    end;
  end;
end;

procedure TFEnvyIpControlMainForm.HandleConnectionClose(var Message: TMessage);
begin
  // this is running in the context of the main thread
  // the socket thread just notified us that the connection was closed by Envy
  if DisconnectButton.Enabled then
    DisconnectButtonClick(nil);
end;

function TFEnvyIpControlMainForm.HandleFileDownload(buf: PAnsiChar; len: integer) : integer;
var fh   : THandle;
    c1   : dword;
    s1   : AnsiString;
    path : array [0..MAX_PATH] of WideChar;
begin
  result := 0;
  if FFileBuf <> nil then begin
    // we're in the process of downloading a file
    // this requires special handling of the incoming data
    result := min(len, FFileLen - FFilePos);
    Move(buf^, FFileBuf[FFilePos], result);
    inc(FFilePos, result);
    if FFilePos = FFileLen then begin
      // file download complete
      s1 := Decode(FFileBuf, FFileLen);
      VirtualFree(FFileBuf, 0, MEM_RELEASE);
      FFilePos := 0;
      FFileLen := 0;
      FFileBuf := nil;
      if FFileCrc = UpdateCrc32(dword(-1), pointer(s1)^, Length(s1)) then begin
        // the CRC matches - great!
        if (ExtractFilePath(FFileFile) = '') and
           (SHGetFolderPathW(0, CSIDL_DESKTOPDIRECTORY, 0, SHGFP_TYPE_CURRENT, path) = S_OK) then
          // if we don't have a file path, we store the downloaded file to the desktop
          FFileFile := UnicodeString(path) + '\' + FFileFile;
        fh := CreateFileW(PWideChar(FFileFile), GENERIC_WRITE, FILE_SHARE_READ, nil, CREATE_ALWAYS, 0, 0);
        if fh <> INVALID_HANDLE_VALUE then begin
          WriteFile(fh, pointer(s1)^, Length(s1), c1, nil);
          CloseHandle(fh);
          case FFileType of
            ft3dlut    : s1 := 'saved downloaded 3DLUT file successfully'#$a;
            ftSettings : s1 := 'saved downloaded Settings file successfully'#$a;
            ftEdid     : s1 := 'saved downloaded EDID file successfully'#$a;
            else         s1 := 'saved downloaded unknown file successfully'#$a;
          end;
          LogMemo.Lines.Add(UnicodeString(s1));
          if (FFileType = ft3dlut) and (FFileSlot > 0) then begin
            inc(FFileSlot);
            if FFileSlot <= SubStrCount(FLutFiles) then begin
              FFileFile := ExtractFilePath(FFileFile) + SubStr(FLutFiles, FFileSlot);
              FFileTick := GetTickCount;
              if not SocketSend(FSocket, 'Download3DLUTFile "' + EncodeUtf8(SubStr(FLutFiles, FFileSlot)) + '"' + #$a) then
                LogMemo.Lines.Add('downloading 3DLUT file failed');
            end else
              FFileSlot := 0;
          end;
        end else begin
          case FFileType of
            ft3dlut    : s1 := 'saving 3DLUT file failed'#$a;
            ftSettings : s1 := 'saving Settings file failed'#$a;
            ftEdid     : s1 := 'saving EDID file failed'#$a;
            else         s1 := 'saving unknown file failed'#$a;
          end;
          LogMemo.Lines.Add(UnicodeString(s1));
        end;
      end else begin
        case FFileType of
          ft3dlut    : s1 := 'downloading 3DLUT file failed (crc mismatch)'#$a;
          ftSettings : s1 := 'downloading Settings file failed (crc mismatch)'#$a;
          ftEdid     : s1 := 'downloading EDID file failed (crc mismatch)'#$a;
          else         s1 := 'downloading unknown file failed (crc mismatch)'#$a;
        end;
        LogMemo.Lines.Add(UnicodeString(s1));
      end;
    end;
  end;
end;

// various helper functions ---------------------------------------------------

const
  LutFilter      = '3DLUT files (*.3dlut)|*.3dlut';
  EdidFilter     = 'EDID blocks (*.edid)|*.edid';
  SettingsFilter = 'Settings files (*.envy)|*.envy';

function TFEnvyIpControlMainForm.DoOpenDialog(title, filters: string; allowMultiSelect: boolean) : string;
var path : array [0..MAX_PATH] of WideChar;
    i1   : integer;
begin
  OpenDialog.Title := title;
  OpenDialog.Filter := filters;
  OpenDialog.FileName := '';
  if allowMultiSelect then
    OpenDialog.Options := OpenDialog.Options + [ofAllowMultiSelect]
  else
    OpenDialog.Options := OpenDialog.Options - [ofAllowMultiSelect];
  if SHGetFolderPathW(0, CSIDL_DESKTOPDIRECTORY, 0, SHGFP_TYPE_CURRENT, path) = S_OK then
    OpenDialog.InitialDir := path;
  if OpenDialog.Execute(Handle) then begin
    if allowMultiSelect then begin
      for i1 := 0 to OpenDialog.Files.Count - 1 do
        result := result + '|' + OpenDialog.Files[i1];
      Delete(result, 1, 1);
    end else
      result := OpenDialog.FileName;
  end else
    result := '';
end;

function TFEnvyIpControlMainForm.DoSaveDialog(title, filters, fileName: string) : string;
var path : array [0..MAX_PATH] of WideChar;
begin
  SaveDialog.Title := title;
  SaveDialog.Filter := filters;
  SaveDialog.FileName := fileName;
  if SHGetFolderPathW(0, CSIDL_DESKTOPDIRECTORY, 0, SHGFP_TYPE_CURRENT, path) = S_OK then
    SaveDialog.InitialDir := path;
  if SaveDialog.Execute(Handle) then begin
    result := SaveDialog.FileName;
    if ExtractFileExt(result) <> ExtractFileExt(SubStr(filters, 2)) then
      result := result + ExtractFileExt(SubStr(filters, 2));
  end else
    result := '';
end;

function TFEnvyIpControlMainForm.PrepareUpload(const fileName: UnicodeString; out crc: dword; out data: AnsiString) : boolean;
var fh  : THandle;
    len : integer;
    buf : pointer;
    c1  : dword;
begin
  result := false;
  fh := CreateFileW(PWideChar(fileName), GENERIC_READ, FILE_SHARE_READ, nil, OPEN_EXISTING, 0, 0);
  if fh <> INVALID_HANDLE_VALUE then begin
    len := GetFileSize(fh, nil);
    buf := VirtualAlloc(nil, len, MEM_COMMIT, PAGE_READWRITE);
    if buf <> nil then begin
      if ReadFile(fh, buf^, len, c1, nil) and (c1 = dword(len)) then begin
        crc := UpdateCrc32(dword(-1), buf^, len);
        data := Encode(buf, len);
        result := true;
      end;
      VirtualFree(buf, 0, MEM_RELEASE);
    end;
    CloseHandle(fh);
  end;
end;

function TFEnvyIpControlMainForm.Enum3dlutFiles : boolean;
var i1 : integer;
begin
  FIgnore3dlut := true;
  FLutFiles := '';
  FLutFilesTemp := '';
  SocketSend(FSocket, 'Enum3DLUTFiles' + #$a);
  // we wait max 3 seconds for the enumeration to complete
  for i1 := 1 to 150 do begin
    Sleep(20);
    Application.ProcessMessages;
    if FLutFiles <> '' then
      break;
  end;
  result := FLutFiles <> '';
end;

// various events -------------------------------------------------------------

procedure TFEnvyIpControlMainForm.FormCreate(Sender: TObject);
var wsaData : TWSADATA;
    ws1     : UnicodeString;
    i64     : int64;
begin
  SetLength(ws1, MAX_PATH);
  GetModuleFileNameW(0, PWideChar(ws1), MAX_PATH);
  i64 := madTools.GetFileVersion(ws1);
  if i64 <> 0 then
    if i64 and $ffff <> 0 then
      Caption := 'Envy IP Control v' + IntToStrExW(i64 shr 48) + '.' + IntToStrExW((i64 shr 32) and $ffff) + '.' + IntToStrExW((i64 shr 16) and $ffff) + '.' + IntToStrExW(i64 and $ffff)
    else
      if i64 and $ffff0000 <> 0 then
        Caption := 'Envy IP Control v' + IntToStrExW(i64 shr 48) + '.' + IntToStrExW((i64 shr 32) and $ffff) + '.' + IntToStrExW((i64 shr 16) and $ffff)
      else
        Caption := 'Envy IP Control v' + IntToStrExW(i64 shr 48) + '.' + IntToStrExW((i64 shr 32) and $ffff);

  // we read any cached information from registry and update the edit boxes accordingly
  if Reg_GetString(HKEY_CURRENT_USER, 'Software\madshi\madVR', 'EnvyIpControl - IpAddr', ws1) then begin
    IpAddrEdit.Text := ws1;
    ActiveControl := ConnectButton;
  end;
  if Reg_GetString(HKEY_CURRENT_USER, 'Software\madshi\madVR', 'EnvyIpControl - Command', ws1) then
    CommandEdit.Text := ws1;
  if Reg_GetString(HKEY_CURRENT_USER, 'Software\madshi\madVR', 'EnvyIpControl - MacAddr', ws1) then
    MacAddrEdit.Text := ws1;
  // initialize WinSock
  ZeroMemory(@wsaData, sizeof(wsaData));
  WSAStartup($201, wsaData);
  // update all the button and edit "Enabled" states
  UpdateControls(nil);
end;

procedure TFEnvyIpControlMainForm.FormKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
begin
  if Key = VK_ESCAPE then begin
    Key := 0;
    Close;
  end else
    if (Key = VK_RETURN) and CommandEdit.Focused and SendCommandButton.Enabled then begin
      Key := 0;
      SendCommandButtonClick(nil);
    end;
end;

procedure TFEnvyIpControlMainForm.CommandEditKeyPress(Sender: TObject; var Key: Char);
begin
  if (Key = #13) or (Key = #27) then
    // avoid beep on RETURN / ESCAPE press
    Key := #0;
end;

procedure TFEnvyIpControlMainForm.HeartbeatTimerTimer(Sender: TObject);
begin
  if FSocket <> 0 then begin
    // we have to send a heartbeat every once in a while
    // otherwise Envy will close the connection
    FIgnoreOk := true;
    SocketSend(FSocket, 'Heartbeat' + #$a);
  end;
end;

procedure TFEnvyIpControlMainForm.UpdateControls(Sender: TObject);
begin
  ConnectButton.Enabled := FSocket = 0;
  DisconnectButton.Enabled := FSocket <> 0;
  WakeButton.Enabled := SubStrCount(MacAddrEdit.Text, '-') = 6;
  PowerOffButton.Enabled := FSocket <> 0;
  StandbyButton.Enabled := FSocket <> 0;
  RestartButton.Enabled := FSocket <> 0;
  StoreInstallerButton.Enabled := FSocket <> 0;
  RestoreInstallerButton.Enabled := FSocket <> 0;
  StoreSuggestedButton.Enabled := FSocket <> 0;
  RestoreSuggestedButton.Enabled := FSocket <> 0;
  StoreUserSlotButton.Enabled := FSocket <> 0;
  RestoreUserSlotButton.Enabled := FSocket <> 0;
  DownloadSettingsButton.Enabled := FSocket <> 0;
  UploadSettingsButton.Enabled := FSocket <> 0;
  EnumLutButton.Enabled := FSocket <> 0;
  RenameLutButton.Enabled := FSocket <> 0;
  DeleteLutButton.Enabled := FSocket <> 0;
  UploadLutButton.Enabled := FSocket <> 0;
  DownloadLutButton.Enabled := FSocket <> 0;
  DownloadCurrentEdidButton.Enabled := FSocket <> 0;
  DownloadEdidSlotButton.Enabled := FSocket <> 0;
  UploadEdidButton.Enabled := FSocket <> 0;
  IncomingSignalButton.Enabled := FSocket <> 0;
  OutgoingSignalButton.Enabled := FSocket <> 0;
  AspectRatioButton.Enabled := FSocket <> 0;
  TemperaturesButton.Enabled := FSocket <> 0;
  SendCommandButton.Enabled := (FSocket <> 0) and (CommandEdit.Text <> '');
  IpAddrEdit.Enabled := FSocket = 0;
  CommandEdit.Enabled := FSocket <> 0;
  if FSocket <> 0 then begin
    IpAddrEdit.Color := clBtnFace;
    CommandEdit.Color := clWindow;
  end else begin
    IpAddrEdit.Color := clWindow;
    CommandEdit.Color := clBtnFace;
  end;
end;

// button click events --------------------------------------------------------

procedure TFEnvyIpControlMainForm.ConnectButtonClick(Sender: TObject);
var tid : dword;
begin
  LogMemo.Lines.Add('attempting to connect to ' + IpAddrEdit.Text + '... <please wait> ...');
  FSocket := SocketCreate(AnsiString(IpAddrEdit.Text), 44077);
  if FSocket <> 0 then begin
    LogMemo.Lines.Add('connecting to ' + IpAddrEdit.Text + ' succeeded');
    // connection was successful - so we store the IP address in the registry
    Reg_SetString(HKEY_CURRENT_USER, 'Software\madshi\madVR', 'EnvyIpControl - IpAddr', IpAddrEdit.Text);
    // update the GUI
    UpdateControls(nil);
    ActiveControl := DisconnectButton;
    // we automatically ask for the MAC address, so we can offer WakeOnLAN
    FIgnoreMac := true;
    SocketSend(FSocket, 'GetMacAddress' + #$a);
    // finally, create a thread to react to incoming data from the Envy
    CloseHandle(CreateThread(nil, 0, @SocketReadThreadProc, self, 0, tid));
  end else
    LogMemo.Lines.Add('connecting to ' + IpAddrEdit.Text + ' failed');
end;

procedure TFEnvyIpControlMainForm.DisconnectButtonClick(Sender: TObject);
begin
  // this function is also called when Envy closes the connection
  SocketClose(FSocket);
  FSocket := 0;
  UpdateControls(nil);
  ActiveControl := ConnectButton;
  LogMemo.Lines.Add('connection closed');
end;

procedure TFEnvyIpControlMainForm.WakeButtonClick(Sender: TObject);
var s1 : AnsiString;
    i1 : integer;
begin
  if SubStrCount(MacAddrEdit.Text, '-') = 6 then begin
    SetLength(s1, 6);
    for i1 := 1 to 6 do
      s1[i1] := AnsiChar(StrToIntDef('$' + SubStr(MacAddrEdit.Text, i1, '-'), 0));
    // the MAC address seems to be valid, so we store it in the registry
    Reg_SetString(HKEY_CURRENT_USER, 'Software\madshi\madVR', 'EnvyIpControl - MacAddr', MacAddrEdit.Text);
    if WakeOnLAN(AnsiString(IpAddrEdit.Text), s1) then
      LogMemo.Lines.Add('sent wake up packet to ' + MacAddrEdit.Text + ' successfully')
    else
      LogMemo.Lines.Add('sending wake up packet to ' + MacAddrEdit.Text + ' failed');
  end;
end;

procedure TFEnvyIpControlMainForm.PowerOffButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'PowerOff' + #$a) then
    LogMemo.Lines.Add('powering off the Envy failed');
end;

procedure TFEnvyIpControlMainForm.StandbyButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'Standby' + #$a) then
    LogMemo.Lines.Add('sending Envy to Standby failed');
end;

procedure TFEnvyIpControlMainForm.RestartButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'Restart' + #$a) then
    LogMemo.Lines.Add('restarting the Envy failed');
end;

procedure TFEnvyIpControlMainForm.StoreInstallerButtonClick(Sender: TObject);
var name, password : string;
begin
  name := 'Installer Settings';
  password := '';
  if DoNamePasswordBox('Store Installer Settings...',
                       'Name/description (reasonably short, please):',
                       name, password) then
    if not SocketSend(FSocket, 'StoreSettings Installer "' + EncodeUtf8(name) + '" "' + EncodeUtf8(password) + '"' + #$a) then
      LogMemo.Lines.Add('storing settings failed');
end;

procedure TFEnvyIpControlMainForm.RestoreInstallerButtonClick(Sender: TObject);
begin
  if MessageBox(Handle, 'Do you really want to restore the Installer Settings?' + #$D#$A + #$D#$A +
                        'The current settings will be lost.', 'Confirmation...', MB_ICONQUESTION or MB_YESNO) = IDYES then
    if not SocketSend(FSocket, 'RestoreSettings Installer' + #$a) then
      LogMemo.Lines.Add('restoring settings failed');
end;

procedure TFEnvyIpControlMainForm.StoreSuggestedButtonClick(Sender: TObject);
var name, password : string;
begin
  name := 'Suggested Settings';
  password := '';
  if DoNamePasswordBox('Store Suggested Settings...',
                       'Name/description (reasonably short, please):',
                       name, password) then
    if not SocketSend(FSocket, 'StoreSettings Suggested "' + EncodeUtf8(name) + '" "' + EncodeUtf8(password) + '"' + #$a) then
      LogMemo.Lines.Add('storing settings failed');
end;

procedure TFEnvyIpControlMainForm.RestoreSuggestedButtonClick(Sender: TObject);
begin
  if MessageBox(Handle, 'Do you really want to restore the Suggested Settings?' + #$D#$A + #$D#$A +
                        'The current settings will be lost.', 'Confirmation...', MB_ICONQUESTION or MB_YESNO) = IDYES then
    if not SocketSend(FSocket, 'RestoreSettings Suggested' + #$a) then
      LogMemo.Lines.Add('restoring settings failed');
end;

procedure TFEnvyIpControlMainForm.StoreUserSlotButtonClick(Sender: TObject);
var slot : integer;
    name : string;
begin
  name := '';
  if DoSlotNameBox('Store Settings to Cloud User Slot...',
                   'Which slot do you want to store the settings to?',
                   'Name/description (reasonably short, please):',
                   'Slot 1|Slot 2|Slot 3|Slot 4|Slot 5|Slot 6|Slot 7|Slot 8|Slot 9|Slot 10|Slot 11|Slot 12|Slot 13|Slot 14|Slot 15|Slot 16',
                   slot, name) then
    if not SocketSend(FSocket, 'StoreSettings ' + IntToStrExA(slot) + ' "' + EncodeUtf8(name) + '"' + #$a) then
      LogMemo.Lines.Add('storing settings failed');
end;

procedure TFEnvyIpControlMainForm.RestoreUserSlotButtonClick(Sender: TObject);
var slot : integer;
begin
  if MessageBox(Handle, 'Do you really want to restore settings from a user slot?' + #$D#$A + #$D#$A +
                        'The current settings will be lost.', 'Confirmation...', MB_ICONQUESTION or MB_YESNO) = IDYES then
    if DoSlotBox('Restore Settings from Cloud User Slot...',
                 'Which slot do you want to restore the settings from?',
                 'Slot 1|Slot 2|Slot 3|Slot 4|Slot 5|Slot 6|Slot 7|Slot 8|Slot 9|Slot 10|Slot 11|Slot 12|Slot 13|Slot 14|Slot 15|Slot 16',
                 slot) then
      if not SocketSend(FSocket, 'RestoreSettings ' + IntToStrExA(slot) + #$a) then
        LogMemo.Lines.Add('restoring settings failed');
end;

procedure TFEnvyIpControlMainForm.DownloadSettingsButtonClick(Sender: TObject);
var fileName : string;
begin
  fileName := DoSaveDialog('Save Downloaded Settings File As...', SettingsFilter, 'Settings');
  if fileName <> '' then begin
    FFileFile := fileName;
    FFileTick := GetTickCount;
    if not SocketSend(FSocket, 'DownloadSettingsFile' + #$a) then
      LogMemo.Lines.Add('downloading Settings file failed');
  end;
end;

procedure TFEnvyIpControlMainForm.UploadSettingsButtonClick(Sender: TObject);
var fileName : string;
    crc      : dword;
    data     : AnsiString;
begin
  if MessageBox(Handle, 'Do you really want to upload Settings to the Envy?' + #$D#$A + #$D#$A +
                        'The current settings will be lost.', 'Confirmation...', MB_ICONQUESTION or MB_YESNO) = IDYES then begin
    fileName := DoOpenDialog('Open Settings File...', SettingsFilter, false);
    if fileName <> '' then
      if (not PrepareUpload(fileName, crc, data)) or
         (not SocketSend(FSocket, 'UploadSettingsFile ' + IntToStrExA(Length(data)) + ' ' + AnsiString(IntToHex(crc, 1)) + #$a)) or
         (not SocketSend(FSocket, data)) then
        LogMemo.Lines.Add('uploading Settings file failed');
  end;
end;

procedure TFEnvyIpControlMainForm.EnumLutButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'Enum3DLUTFiles' + #$a) then
    LogMemo.Lines.Add('enumerating 3DLUT files failed');
end;

procedure TFEnvyIpControlMainForm.RenameLutButtonClick(Sender: TObject);
var slot : integer;
    name : string;
begin
  if Enum3dlutFiles then begin
    name := '';
    if DoSlotNameBox('Rename 3DLUT File...',
                     'Which 3DLUT file to you want to rename?',
                     'New file name (reasonably short, please):',
                     FLutFiles,
                     slot, name) then
      if not SocketSend(FSocket, 'Rename3DLUTFile "' + EncodeUtf8(SubStr(FLutFiles, slot)) + '" "' + EncodeUtf8(name) + '"' + #$a) then
        LogMemo.Lines.Add('renaming 3DLUT file failed');
  end;
end;

procedure TFEnvyIpControlMainForm.DeleteLutButtonClick(Sender: TObject);
var luts : UnicodeString;
    slot : integer;
begin
  if Enum3dlutFiles then begin
    luts := FLutFiles;
    if SubStrCount(FLutFiles) > 1 then
      luts := luts + '|all 3DLUT files';
    if DoSlotBox('Delete 3DLUT File...', 'Which 3DLUT file to you want to delete?', luts, slot) then
      if slot > SubStrCount(FLutFiles) then begin
        if MessageBox(Handle, 'Do you really want to delete all 3DLUT files?' + #$D#$A + #$D#$A +
                              'The files will be physically deleted from the Envy.', 'Confirmation...', MB_ICONQUESTION or MB_YESNO) = IDYES then
          for slot := 1 to SubStrCount(FLutFiles) do
            if not SocketSend(FSocket, 'Delete3DLUTFile "' + EncodeUtf8(SubStr(FLutFiles, slot)) + '"' + #$a) then
              LogMemo.Lines.Add('deleting 3DLUT file "' + SubStr(FlutFiles, slot) + '" failed');
      end else
        if MessageBox(Handle, 'Do you really want to delete this 3DLUT file?' + #$D#$A + #$D#$A +
                              'The file will be physically deleted from the Envy.', 'Confirmation...', MB_ICONQUESTION or MB_YESNO) = IDYES then
          if not SocketSend(FSocket, 'Delete3DLUTFile "' + EncodeUtf8(SubStr(FLutFiles, slot)) + '"' + #$a) then
            LogMemo.Lines.Add('deleting 3DLUT file failed');
  end;
end;

procedure TFEnvyIpControlMainForm.UploadLutButtonClick(Sender: TObject);
var files    : string;
    fileName : string;
    name     : string;
    crc      : dword;
    data     : AnsiString;
    i1, i2   : integer;
begin
  files := DoOpenDialog('Open 3DLUT File...', LutFilter, true);
  if files <> '' then begin
    if SubStrCount(files) > 1 then
      LogMemo.Lines.Add('uploading ' + IntToStr(SubStrCount(files)) + ' 3DLUT files, please wait...');
    for i1 := 1 to SubStrCount(files) do begin
      fileName := SubStr(files, i1);
      name := ExtractFileName(fileName);
      DeleteRW(name, Length(ExtractFileExt(name)));
      if SubTextExists(FLutFiles, name + '.3dlut') then
        // the Envy already has a 3DLUT file with this name
        // in order to not overwrite it, we add a "(2)" to the file name
        for i2 := 2 to 1000 do
          if not SubTextExistsW(FLutFiles, name + ' (' + IntToStrExW(i2) + ').3dlut') then begin
            name := name + ' (' + IntToStrExW(i2) + ').3dlut';
            break;
          end;
      if (not PrepareUpload(fileName, crc, data)) or
         (not SocketSend(FSocket, 'Upload3DLUTFile ' + IntToStrExA(Length(data)) + ' ' + AnsiString(IntToHex(crc, 1)) + ' "' + EncodeUtf8(name) + '"' + #$a)) or
         (not SocketSend(FSocket, data)) then begin
        LogMemo.Lines.Add('uploading 3DLUT file failed');
        break;
      end;
      Application.ProcessMessages;
    end;
    if SubStrCount(files) > 1 then
      LogMemo.Lines.Add('uploading ' + IntToStr(SubStrCount(files)) + ' 3DLUT files done');
  end;
end;

procedure TFEnvyIpControlMainForm.DownloadLutButtonClick(Sender: TObject);
var luts     : UnicodeString;
    fileName : string;
    slot     : integer;
begin
  if Enum3dlutFiles then begin
    luts := FLutFiles;
    if SubStrCount(FLutFiles) > 1 then
      luts := luts + '|all 3DLUT files';
    if DoSlotBox('Download 3DLUT File...', 'Which 3DLUT file do you want to download?', luts, slot) then
      if slot > SubStrCount(FLutFiles) then begin
        fileName := DoSaveDialog('Save Downloaded 3DLUT File As...', LutFilter, SubStr(FLutFiles, 1));
        if fileName <> '' then begin
          FFileFile := fileName;
          FFileSlot := 1;
          FFileTick := GetTickCount;
          if not SocketSend(FSocket, 'Download3DLUTFile "' + EncodeUtf8(SubStr(FLutFiles, 1)) + '"' + #$a) then
            LogMemo.Lines.Add('downloading 3DLUT file failed');
        end;
      end else begin
        fileName := DoSaveDialog('Save Downloaded 3DLUT File As...', LutFilter, SubStr(FLutFiles, slot));
        if fileName <> '' then begin
          FFileFile := fileName;
          FFileSlot := 0;
          FFileTick := GetTickCount;
          if not SocketSend(FSocket, 'Download3DLUTFile "' + EncodeUtf8(SubStr(FLutFiles, slot)) + '"' + #$a) then
            LogMemo.Lines.Add('downloading 3DLUT file failed');
        end;
      end;
  end;
end;

procedure TFEnvyIpControlMainForm.DownloadCurrentEdidButtonClick(Sender: TObject);
var fileName : string;
begin
  fileName := DoSaveDialog('Save Downloaded EDID Block As...', EdidFilter, 'Downloaded');
  if fileName <> '' then begin
    FFileFile := fileName;
    FFileTick := GetTickCount;
    if not SocketSend(FSocket, 'DownloadEDIDFile Current' + #$a) then
      LogMemo.Lines.Add('downloading EDID block failed');
  end;
end;

procedure TFEnvyIpControlMainForm.DownloadEdidSlotButtonClick(Sender: TObject);
var slot     : integer;
    fileName : string;
begin
  if DoSlotBox('Download EDID Slot...',
               'Which EDID Slot do you want to download?',
               'Slot 1|Slot 2|Slot 3|Slot 4|Slot 5|Slot 6|Slot 7|Slot 8',
               slot) then begin
    fileName := DoSaveDialog('Save Downloaded EDID Block As...', EdidFilter, 'Downloaded');
    if fileName <> '' then begin
      FFileFile := fileName;
      FFileTick := GetTickCount;
      if not SocketSend(FSocket, 'DownloadEDIDFile ' + IntToStrExA(slot) + #$a) then
        LogMemo.Lines.Add('downloading EDID block failed');
    end;
  end;
end;

procedure TFEnvyIpControlMainForm.UploadEdidButtonClick(Sender: TObject);
var slot     : integer;
    name     : string;
    fileName : string;
    crc      : dword;
    data     : AnsiString;
begin
  name := '';
  fileName := DoOpenDialog('Open EDID Block...', EdidFilter, false);
  if (fileName <> '') and
     DoSlotNameBox('Upload EDID File...',
                   'Which slot do you want to upload the EDID block to?',
                   'Name/description (reasonably short, please):',
                   'Slot 1|Slot 2|Slot 3|Slot 4|Slot 5|Slot 6|Slot 7|Slot 8',
                   slot, name) then
    if (not PrepareUpload(fileName, crc, data)) or
       (not SocketSend(FSocket, 'UploadEDIDFile ' + IntToStrExA(slot) + ' ' + IntToStrExA(Length(data)) + ' ' + AnsiString(IntToHex(crc, 1)) + ' "' + EncodeUtf8(name) + '"' + #$a)) or
       (not SocketSend(FSocket, data)) then
      LogMemo.Lines.AdD('uploading EDID block failed');
end;

procedure TFEnvyIpControlMainForm.RemoteBmpMouseDown(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
var s1 : AnsiString;
begin
  FButtonDown := '';
  ButtonDownTimer.Enabled := false;
  s1 := '';
  if (X >= 44) and (X <= 94) and (Y >= 150) and (Y <= 199) then
    s1 := 'OK'
  else
    if ((X >= 48) and (X <= 90) and (Y >= 113) and (Y <= 147)) then
      s1 := 'UP'
    else
      if (X >= 8) and (X <= 42) and (Y >= 153) and (Y <= 196) then
        s1 := 'LEFT'
      else
        if (X >= 96) and (X <= 130) and (Y >= 153) and (Y <= 196) then
          s1 := 'RIGHT'
        else
          if (X >= 48) and (X <= 90) and (Y >= 201) and (Y <= 234) then
            s1 := 'DOWN'
          else
            if (Y >= 20) and (Y <= 60) then begin
              if (X >= 19) and (X <= 60) then
                s1 := 'POWER'
              else
                if (Y >= 23) and (Y <= 57) and (X >= 81) and (X <= 116) then
                  s1 := 'INFO';
            end else
              if (Y >= 75) and (Y <= 106) then begin
                if (X >= 11) and (X <= 66) then
                  s1 := 'MENU'
                else
                  if (X >= 72) and (X <= 127) then
                    s1 := 'SETTINGS';
              end else
                if (Y >= 242) and (Y <= 275) then begin
                  if (X >= 11) and (X <= 66) then
                    s1 := 'INPUT'
                  else
                    if (X >= 72) and (X <= 127) then
                      s1 := 'BACK';
                end else
                  if (Y >= 290) and (Y <= 331) then begin
                    if (X >= 19) and (X <= 60) then
                      s1 := 'RED'
                    else
                      if (X >= 78) and (X <= 119) then
                        s1 := 'GREEN';
                  end else
                    if (Y >= 341) and (Y <= 381) then begin
                      if (X >= 19) and (X <= 60) then
                        s1 := 'BLUE'
                      else
                        if (X >= 78) and (X <= 119) then
                          s1 := 'YELLOW';
                    end else
                      if (Y >= 391) and (Y <= 431) then
                        if (X >= 19) and (X <= 60) then
                          s1 := 'MAGENTA'
                        else
                          if (X >= 78) and (X <= 119) then
                            s1 := 'CYAN';
  if (s1 <> 'OK') and (s1 <> 'MENU') and (s1 <> 'LEFT') and (s1 <> 'RIGHT') and (s1 <> 'UP') and (s1 <> 'DOWN') then begin
    FButtonDown := s1;
    ButtonDownTimer.Interval := 600;
    ButtonDownTimer.Enabled := true;
  end else
    if SocketSend(FSocket, 'KeyPress ' + s1 + #$a) then begin
      if (s1 = 'LEFT') or (s1 = 'RIGHT') or (s1 = 'UP') or (s1 = 'DOWN') then begin
        FButtonDown := s1;
        ButtonDownTimer.Interval := 600;
        ButtonDownTimer.Enabled := true;
      end;
    end else
      LogMemo.Lines.Add('pressing button ' + string(s1) + ' failed');
end;

procedure TFEnvyIpControlMainForm.ButtonDownTimerTimer(Sender: TObject);
var s1 : AnsiString;
begin
  s1 := FButtonDown;
  if (s1 <> 'LEFT') and (s1 <> 'RIGHT') and (s1 <> 'UP') and (s1 <> 'DOWN') then begin
    FButtonDown := '';
    ButtonDownTimer.Enabled := false;
    if (s1 <> '') and (not SocketSend(FSocket, 'KeyHold ' + s1 + #$a)) then
      LogMemo.Lines.Add('holding button ' + string(s1) + ' failed');
  end else begin
    if ButtonDownTimer.Interval > 200 then
      ButtonDownTimer.Interval := 200
    else
      if ButtonDownTimer.Interval > 40 then
        ButtonDownTimer.Interval := ButtonDownTimer.Interval * 19 div 20;
    FIgnoreOk := true;
    if (s1 <> '') and (not SocketSend(FSocket, 'KeyPress ' + s1 + #$a)) then
      LogMemo.Lines.Add('pressing button ' + string(s1) + ' failed');
  end;
end;

procedure TFEnvyIpControlMainForm.RemoteBmpMouseUp(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
var s1 : AnsiString;
begin
  s1 := FButtonDown;
  FButtonDown := '';
  ButtonDownTimer.Enabled := false;
  if (s1 <> '') and (s1 <> 'LEFT') and (s1 <> 'RIGHT') and (s1 <> 'UP') and (s1 <> 'DOWN') then
    if not SocketSend(FSocket, 'KeyPress ' + s1 + #$a) then
      LogMemo.Lines.Add('pressing button ' + string(s1) + ' failed');
end;

procedure TFEnvyIpControlMainForm.IncomingSignalButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'GetIncomingSignalInfo' + #$a) then
    LogMemo.Lines.Add('asking for incoming signal info failed');
end;

procedure TFEnvyIpControlMainForm.OutgoingSignalButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'GetOutgoingSignalInfo' + #$a) then
    LogMemo.Lines.Add('asking for outgoing signal info failed');
end;

procedure TFEnvyIpControlMainForm.AspectRatioButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'GetAspectRatio' + #$a) then
    LogMemo.Lines.Add('asking for aspect ratio failed');
end;

procedure TFEnvyIpControlMainForm.TemperaturesButtonClick(Sender: TObject);
begin
  if not SocketSend(FSocket, 'GetTemperatures' + #$a) then
    LogMemo.Lines.Add('asking for temperatures failed');
end;

procedure TFEnvyIpControlMainForm.SendCommandButtonClick(Sender: TObject);
begin
  if SocketSend(FSocket, EncodeUtf8(CommandEdit.Text) + #$a) then
    // we sent the command successfully, so we store it to the registry
    Reg_SetString(HKEY_CURRENT_USER, 'Software\madshi\madVR', 'EnvyIpControl - Command', CommandEdit.Text)
  else
    LogMemo.Lines.Add('sending command "' + CommandEdit.Text + '" failed');
end;

end.
