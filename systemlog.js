var log_level_error = "Error";
var log_level_warning = "Warning";
var log_level_notice = "Notice";
var log_level_info = "Info";
var log_type_all = 0;
var log_type_user = 1<<1;
var log_type_system = 1<<3;
var log_type_security = (1<<22)+(1<<4);
var TIMEOUT = 3000;
function getNewLog() {
getAjaxData("api/log/loginfo", function($xml) {
var res = xml2object($xml);
if (res.type == 'response') {
var log = res.response;
var content = log.LogContent;
content = XSSResolveCannotParseChar(content);
content = content.replace(/&lt;br&#x2F;&gt;/g, '<br/>');
content = content.replace(/&#40;/g, '(');
content = content.replace(/&#41;/g, ')');
$("#type_select").val(log.DisplayType);
$("#level_select").val(log.DisplayLevel);
function getSpaceIndex(s,i) {
var b=0;
for(var k=0;k<s.length;k++) {
if(s[k]==" ") {
b++;
if(b==i)
return k;
}
}
}
if(content) {
content=content.replace(/\\r\\n$/,'');
window.a1=content.split(/\\r\\n/);
window.b1=[];
var k1="";
for(var i in a1) {
tmp=[];
tmp.push(a1[i].substring(0,getSpaceIndex(a1[i],2)));
tmp.push(a1[i].substring(getSpaceIndex(a1[i], 2)+1, getSpaceIndex(a1[i], 3)));
tmp.push(a1[i].substring(getSpaceIndex(a1[i], 3)+1, getSpaceIndex(a1[i], 4)));
tmp.push(a1[i].substring(getSpaceIndex(a1[i], 4)+1));
b1.push(tmp);
}
for(var i in b1) {
k2="";
for(var k in b1[i]) {
k2+="<td>"+b1[i][k]+"</td>";
}
k2="<tr>"+k2+"</tr>";
k1+=k2;
}
}
$("table#show_log_table").empty().append(k1);
var na=navigator.userAgent;
if(/Safari/.test(na)) {
$("#show_log_table_header div:nth-child(1)").css('width','139px');
$("#show_log_table_header div:nth-child(2),#show_log_table_header div:nth-child(3)").css('width','59px');
$("#show_log_table_header div:nth-child(4)").css('width','324px');
if((LANGUAGE_DATA.current_language == 'ar_sa' || LANGUAGE_DATA.current_language == 'he_il' || LANGUAGE_DATA.current_language == 'fa_fa')&&!/Chrome/.test(na)) {
$("#show_log_table_header div:nth-child(1)").css('width','149px');
$("#show_log_table_header div:nth-child(4)").css('width','314px');
}else if(LANGUAGE_DATA.current_language=='zh_cn'){
setTimeout(function(){
$("#show_log_table_header div:nth-child(1),").css('width',$("#show_log_table tr td:nth-child(1)").css('width'));
$("#show_log_table_header div:nth-child(2),#show_log_table_header div:nth-child(3)").css('width',$("#show_log_table td:nth-child(2)").css('width'));
},10);
}
} else {
if(/IE/.test(na))
$("#show_log_table th").hide();
if(/IE\s8/.test(na)) {
$("table#show_log_table td:nth-child(1)").css('width','140px');
$("table#show_log_table td:nth-child(2),table#show_log_table td:nth-child(3)").css('width','60px');
}
$("#show_log_table_header div:nth-child(1)").css('width','139px');
$("#show_log_table_header div:nth-child(2),#show_log_table_header div:nth-child(3)").css('width','59px');
$("#show_log_table_header div:nth-child(4)").css('width','314px');
}
}
}, {
sync : true
}
);
}
function getConfigType(){
var html = "";
html += "<option value = '"+log_type_all+"'>"+eval("log_type_"+0)+"</option>";
html += "<option value = '"+log_type_user+"'>"+eval("log_type_"+1)+"</option>";
html += "<option value = '"+log_type_system+"'>"+eval("log_type_"+2)+"</option>";
html += "<option value = '"+log_type_security+"'>"+eval("log_type_"+3)+"</option>";
$("#type_select").append(html);
}
function getConfigLevel(){
var html = "";
html += "<option value = '"+log_level_warning+"'>"+eval("log_level_"+1)+"</option>";
html += "<option value = '"+log_level_notice+"'>"+eval("log_level_"+2)+"</option>";
html += "<option value = '"+log_level_info+"'>"+eval("log_level_"+3)+"</option>";
$("#level_select").append(html);
}
function getCurrentLog(){
var g_type_select = $("#type_select").val();
var g_level_select = $("#level_select").val();
var apply_level = {
DisplayType : g_type_select,
DisplayLevel : g_level_select
};
var apply_req = object2xml('request',apply_level);
showWaitingDialog(common_waiting, IDS_systemlog_get_info);
saveAjaxData('api/log/loginfo', apply_req, function($xml){
var ret = xml2object($xml);
if(isAjaxReturnOK(ret)){
closeWaitingDialog();
} else {
closeWaitingDialog();
showInfoDialog(common_fail);
}
getNewLog();
});
}
$(document).ready(function(){
getConfigType();
getConfigLevel();
getNewLog();
$('#type_select').change( function() {
getCurrentLog();
});
$('#level_select').change( function() {
getCurrentLog();
});
});
