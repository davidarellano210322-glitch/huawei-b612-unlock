var MACRO_ENABLE = '1';
var TR069_FILE_INTERVAL = 3000;
var TR069_ROOTCERT = "0";
var TR069_NEW_CERT = "";
function controlIntervalEnable(boolFlag) {
if (boolFlag) {
$('#input_tr069_interval').removeAttr('disabled');
} else {
$('#input_tr069_interval').attr('disabled', true);
}
}
function controlCertificateEnable(boolFlag) {
if (boolFlag) {
$("#certificate_uplaod_tr").show();
} else {
$("#certificate_uplaod_tr").hide();
$("#certificate_uplaod_tr").next().hide();
}
}
function checkUploadCertifiateName() {
var uploadFileName = $('#up_nodite').val();
var reg = /\.pem$|\.crt$/i;
clearAllErrorLabel();
if (reg.test(uploadFileName)) {
button_enable('apply_button', '1');
} else {
showErrorUnderTextbox('form_tr069', system_hint_file_name_empty);
$('#up_nodite').val("");
}
}
var g_specialPortArray = '';
function initPageData() {
$(".tr069_enable ~ tr").hide();
getAjaxData("api/cwmp/basic-info", function($xml) {
var ret = xml2object($xml);
if ('response' == ret.type) {
var tr069_info = ret.response;
if (typeof(tr069_info.virtualserver_used_wanport) != 'undefined' && tr069_info.virtualserver_used_wanport != '') {
g_specialPortArray = tr069_info.virtualserver_used_wanport;
} else {
g_specialPortArray = '';
}
g_specialPortArray = g_specialPortArray.split(', ');
$("input[name='radio_tr069_enable'][value=" + tr069_info.enable+ ']').attr('checked', true);
$("input[name='radio_tr069_notice'][value=" + tr069_info.inform+ ']').attr('checked', true);
$("#input_tr069_interval").val(tr069_info.interval);
$("#input_tr069_acs_url").val(tr069_info.acsurl);
$("#input_tr069_acs_name").val(tr069_info.acsname);
$("#input_tr069_acs_password").val(tr069_info.acspwd);
$("#input_tr069_con_name").val(tr069_info.conname);
$("#input_tr069_con_password").val(tr069_info.conpwd);
$("#input_tr069_con_port").val(tr069_info.conport);
$("input[name='radio_tr069_certificate'][value=" + tr069_info.cert+ ']').attr('checked', true);
if(tr069_info.enable == "0"){
$(".tr069_enable ~ tr").hide();
}else{
$(".tr069_enable ~ tr").show();
}
TR069_ROOTCERT = tr069_info.iscwmpcertexisted;
controlIntervalEnable(MACRO_ENABLE == tr069_info.inform);
controlCertificateEnable((MACRO_ENABLE == tr069_info.cert) && ("0" != tr069_info.enable));
} else if (ret.error.code == ERROR_SYSTEM_BUSY) {
showInfoDialog(common_system_busy);
} else {
showInfoDialog(common_fail);
}
});
}
function checkACS_ipFormat(a) {
if(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\:\d+)?$/.test(a)) {
if(a.indexOf(':')>-1) {
var port=a.substring(a.lastIndexOf(':')+1);
if(!(0<=port&&port<=65535) || /^0\d+/.test(port)){
return false;
}
a=a.replace(/(\:\d+)/,'');
}
var index=[];
for(var i=0;i<a.length;i++) {
if(a[i]=='.') {
index.push(i);
}
}
var a1=a.substring(0,index[0]);
var b1=a.substring(index[0]+1,index[1]);
var c1=a.substring(index[1]+1,index[2]);
var d1=a.substring(index[2]+1);
if(!(/^0[0-9]{1,2}$/.test(a1) || /^0[0-9]{1,2}$/.test(b1) || /^0[0-9]{1,2}$/.test(c1) || /^0[0-9]{1,2}$/.test(d1))) {
if((a1>=1&&a1<224&&a1!=127) && (b1>=0&&b1<=255) && (c1>=0&&c1<=255) && (d1>=0&&d1<255)) {
return true;
} else {
return false;
}
} else {
return false;
}
} else {
return false;
}
}
function validInputData() {
var retFlag = true;
var tempStr = "";
var rgExp;
clearAllErrorLabel();
rgExp = /^[0-9]*$/;
tempStr = $.trim($("#input_tr069_interval").val());
if((tempStr == "" || !rgExp.test(tempStr)) && MACRO_ENABLE == $("[name='radio_tr069_notice']:checked").val()) {
showErrorUnderTextbox("input_tr069_interval", IDS_statistics_aglie_number);
return false;
}
if((parseInt(tempStr,10) > 2678400 || parseInt(tempStr,10) < 120) && MACRO_ENABLE == $("[name='radio_tr069_notice']:checked").val()) {
showErrorUnderTextbox("input_tr069_interval", IDS_tr069_notice_timerange);
return false;
}
rgExp = /^((https|http):\/\/)[a-zA-Z0-9\.\-\:\/\[\]]{1,}$/;
tempStr = $.trim($("#input_tr069_acs_url").val());
if(tempStr == "" || !rgExp.test(tempStr)) {
showErrorUnderTextbox("input_tr069_acs_url", IDS_tr069_urlfilter_error_2);
return false;
}
if(/^(https|http):\/\/[\d\.]+(\:)?/.test(tempStr)) {
if(!checkACS_ipFormat(tempStr.replace(/^(http|https):\/\/([\d\.]+(\:\d+)?)(\/.*)?$/,'$2'))) {
showErrorUnderTextbox("input_tr069_acs_url", IDS_tr069_urlfilter_error_2);
return false;
}
}
tempStr = $.trim($("#input_tr069_acs_name").val());
if(tempStr == "" || !checkInputChar(tempStr)) {
showErrorUnderTextbox("input_tr069_acs_name", dialup_hint_user_name_valid_char);
return false;
}
tempStr = $.trim($("#input_tr069_acs_password").val());
if(tempStr == "" || !checkInputChar(tempStr)) {
showErrorUnderTextbox("input_tr069_acs_password", dialup_hint_password_valid_char);
return false;
}
tempStr = $.trim($("#input_tr069_con_name").val());
if(tempStr == "" || !checkInputChar(tempStr)) {
showErrorUnderTextbox("input_tr069_con_name", dialup_hint_user_name_valid_char);
return false;
}
tempStr = $.trim($("#input_tr069_con_password").val());
if(tempStr == "" || !checkInputChar(tempStr)) {
showErrorUnderTextbox("input_tr069_con_password", dialup_hint_password_valid_char);
return false;
}
tempStr = $.trim($("#input_tr069_con_port").val());
if (tempStr == "" || isNaN(tempStr) || (parseInt(tempStr, 10) < 1) || (parseInt(tempStr, 10) > 65535)) {
showErrorUnderTextbox("input_tr069_con_port", IDS_normclass_port_error);
return false;
}
if (!checkInputPort(tempStr)) {
showErrorUnderTextbox("input_tr069_con_port", IDS_tr069_con_port_error);
return false;
}
if (!checkSpecialPort(tempStr)) {
showErrorUnderTextbox("input_tr069_con_port", IDS_tr069_spcial_port_prompt);
return false;
}
tempStr = $.trim($("#up_nodite").val());
TR069_NEW_CERT = tempStr;
if(TR069_ROOTCERT == "0" && tempStr == "" && MACRO_ENABLE == $("[name='radio_tr069_certificate']:checked").val()) {
showErrorUnderTextbox('form_tr069', system_hint_file_name_empty);
return false;
}
return retFlag;
}
function uploadCertificateFile() {
var optionst = {
async: true,
url: '/api/service/uploadcertification',
success: function(responseText, statusText) {
var data = responseText;
var xml;
if (typeof data == 'string' || typeof data == 'number') {
if (!window.ActiveXObject) {
var parser = new DOMParser();
xml = parser.parseFromString(data, 'text/xml');
} else {
xml = new ActiveXObject('Microsoft.XMLDOM');
xml.async = false;
xml.loadXML(data);
}
} else {
xml = data;
}
var ret = xml2object($(xml));
if (ret.type == 'response' && ret.response == 'OK') {
setTimeout( function() {
postData();
},TR069_FILE_INTERVAL);
} else {
closeWaitingDialog();
showErrorUnderTextbox('form_tr069', system_hint_file_name_empty);
}
}
};
if($.isArray(g_requestVerificationToken)) {
if(g_requestVerificationToken.length > 0) {
$('#tr069_csrf_token').val('csrf:' + g_requestVerificationToken[0]);
} else {
setTimeout(function () {
uploadCertificateFile();
}, 50)
return;
}
}
$('#form_tr069').ajaxSubmit(optionst);
}
function postData() {
var request = null;
if(MACRO_ENABLE == $("[name='radio_tr069_enable']:checked").val()?"1":"0"){
request = {
"enable": MACRO_ENABLE == $("[name='radio_tr069_enable']:checked").val()?"1":"0",
"interval":$("#input_tr069_interval").val(),
"acsurl":$("#input_tr069_acs_url").val(),
"acsname":$("#input_tr069_acs_name").val(),
"acspwd":$("#input_tr069_acs_password").val(),
"conname":$("#input_tr069_con_name").val(),
"inform":MACRO_ENABLE == $("[name='radio_tr069_notice']:checked").val()?"1":"0",
"conpwd":$("#input_tr069_con_password").val(),
"conport":$("#input_tr069_con_port").val(),
"cert":MACRO_ENABLE == $("[name='radio_tr069_certificate']:checked").val()?"1":"0"
};
}else{
request = {
"enable": MACRO_ENABLE == $("[name='radio_tr069_enable']:checked").val()?"1":"0"
}
}
if (checkPostIndex(0)) {
delete request.acspwd;
}
if (checkPostIndex(1)) {
delete request.conpwd;
}
var xml = object2xml('request', request);
saveAjaxData("api/cwmp/basic-info", xml, function($xml) {
mousedownIndexList = [];
var ret = xml2object($xml);
closeWaitingDialog();
if (isAjaxReturnOK(ret)) {
button_enable('apply_button', '0');
showInfoDialog(common_settings_successfull);
} else {
showInfoDialog(common_failed);
}
initPageData();
},{
enc:true
});
}
function applySetDate() {
if(MACRO_ENABLE == $("[name='radio_tr069_enable']:checked").val()){
if(validInputData()){
showWaitingDialog(common_waiting, sd_hint_wait_a_few_moments);
if("" != TR069_NEW_CERT && MACRO_ENABLE == $("[name='radio_tr069_certificate']:checked").val()) {
uploadCertificateFile();
} else {
setTimeout( function() {
postData();
},TR069_FILE_INTERVAL);
}
}
}else{
showWaitingDialog(common_waiting, sd_hint_wait_a_few_moments);
setTimeout( function() {
postData();
},TR069_FILE_INTERVAL);
}
}
function checkInputPort(port){
var i = 0;
var aSpecialPort = ["21","22","23","25","80","443","135","53","161"];
for (i=0;i<aSpecialPort.length;i++) {
if(port == aSpecialPort[i]){
return false;
}
}
return true;
}
function checkSpecialPort(port) {
var i = 0;
var portArr = [];
for (i=0;i<g_specialPortArray.length;i++) {
portArr = g_specialPortArray[i].split('-');
if (parseInt(port,10) >= parseInt(portArr[0],10) && parseInt(port,10) <= parseInt(portArr[1],10)) {
return false;
}
}
return true;
}
$(document).ready( function() {
clickPasswordEvent('input_tr069_acs_password',0);
clickPasswordEvent('input_tr069_con_password',1);
button_enable('apply_button', '0');
initPageData();
$("input[name='radio_tr069_enable']").click( function() {
var tr069Enable = $("[name='radio_tr069_enable']:checked").val();
if(tr069Enable == "0"){
$(".tr069_enable ~ tr").hide();
}else{
$(".tr069_enable ~ tr").show();
}
var tr069inform = $("[name='radio_tr069_notice']:checked").val();
var tr069cert = $("[name='radio_tr069_certificate']:checked").val();
controlIntervalEnable(MACRO_ENABLE == tr069inform);
controlCertificateEnable((MACRO_ENABLE == tr069cert) && ("0" != tr069Enable));
button_enable('apply_button', '1');
});
$("input[name='radio_tr069_notice']").click( function() {
controlIntervalEnable(MACRO_ENABLE == $("[name='radio_tr069_notice']:checked").val());
button_enable('apply_button', '1');
});
$("input[name='radio_tr069_certificate']").click( function() {
controlCertificateEnable(MACRO_ENABLE == $("[name='radio_tr069_certificate']:checked").val());
button_enable('apply_button', '1');
});
$('#up_nodite').change( function() {
var uploadFileName = $('#up_nodite').val();
if (uploadFileName.indexOf('\\') > -1) {
uploadFileName = uploadFileName.substring(uploadFileName.lastIndexOf('\\') + 1);
}
$('#textbox_path').val('OU:' + uploadFileName);
checkUploadCertifiateName();
});
$("#apply_button").click( function() {
if(!isButtonEnable('apply_button')) {
return;
}
applySetDate();
});
$('#input_tr069_interval, #input_tr069_acs_url, #input_tr069_acs_name, #input_tr069_acs_password, #input_tr069_con_name, #input_tr069_con_password, #input_tr069_con_port').bind('change input paste cut keydown', function(e) {
if(MACRO_KEYCODE != e.keyCode) {
button_enable('apply_button', '1');
}
});
});
