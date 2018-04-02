function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 点击退出按钮时执行的函数
function logout() {
    $.ajax({
        url: "/api/v1_0/sessions",
        type: "delete",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        dataType: "json",
        success: function (resp) {
            if (resp.errno == 0) {
                location.href = "/index.html";
            } else {
                alert(resp.errmsg)
            }
        }
    });
}

$(document).ready(function () {
})