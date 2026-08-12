var g_timerRestore = 1000;
var g_voicebusy = null;
function gotoLoginWhileSystemUp() {
if (DATA_READY.statusReady) {
gotoPageWithoutHistory('home.html');
}
}
function do_restore() {
var request = {
Control: 2
};
var DEFAULT_GATEWAY_IP = '';
getConfigData('config/lan/config.xml', function($xml) {
var ret = xml2object($xml);
if ('config' == ret.type) {
DEFAULT_GATEWAY_IP = ret.config.dhcps.ipaddress;
}
}, {
sync: true
}
);
var xmlstr = object2xml('request', request);
saveAjaxData('api/device/control', xmlstr, function($xml) {
var xmlstr = xml2object($xml);
if (isAjaxReturnOK(xmlstr)) {
ping_setPingAddress(DEFAULT_GATEWAY_IP);
setTimeout(startPing, 50000);
} else {
closeWaitingDialog();
showInfoDialog(common_failed);
return false;
}
});
}
function restore() {
showWaitingDialog(common_waiting, sd_hint_wait_a_few_moments);
clearTimeout(g_decive_timer);
clearTimeout(g_simcard_timer);
clearTimeout(g_heart_beat_timer);
setTimeout(do_restore, g_timerRestore);
}
$( function() {
$('#button_restore').bind('click', function() {
if (!isButtonEnable('restore_apply_button')) {
return;
}
button_enable('restore_apply_button', '0');
if(isneedvoicbusy()){
getAjaxData("api/voice/voicebusy", function($xml) {
var gstatus_ret = xml2object($xml);
if(gstatus_ret.type == "response") {
g_voicebusy = gstatus_ret;
}
}, {
sync: true
});
if(g_voicebusy.response == 'Busy'){
gotoPageWithoutHistory(VOICE_BUSY_URL);
return;
}
}
showConfirmDialog(system_hint_restore, restore, function() {
button_enable('restore_apply_button', '1');
},null, function() {
button_enable('restore_apply_button', '1');
});
return false;
});
});
