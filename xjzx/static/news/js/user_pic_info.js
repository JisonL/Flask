function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $('.pic_info').submit(function (e) {
        e.preventDefault();
        $(this).ajaxSubmit({
            url:'/user/pic',
            type:'post',
            dataType:'json',
            success:function (data) {
                if(data.result==1){

                    $('.now_user_pic').attr('src',data.avatar);
                    $('.user_center_avatar',parent.document).attr('src',data.avatar);
                    $('.login_pic',parent.document).attr('src',data.avatar);
                }
            }
        });
    });
})