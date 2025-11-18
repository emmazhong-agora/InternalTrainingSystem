# -*- coding: utf-8 -*-
__copyright__ = "Copyright (c) 2014-2017 Agora.io, Inc."

from .AccessToken2 import *


# RECOMMENDED. Use this role for a voice/video call or a live broadcast, if
# your scenario does not require authentication for
# [Co-host](https://docs.agora.io/en/video-calling/get-started/authentication-workflow?#co-host-token-authentication).
Role_Publisher = 1

# Only use this role if your scenario require authentication for
# [Co-host](https://docs.agora.io/en/video-calling/get-started/authentication-workflow?#co-host-token-authentication).
# @note In order for this role to take effect, please contact our support team
# to enable authentication for Hosting-in for you. Otherwise, Role_Subscriber
# still has the same privileges as Role_Publisher.
Role_Subscriber = 2


class RtcTokenBuilder:
    @staticmethod
    def build_token_with_uid(app_id, app_certificate, channel_name, uid, role, token_expire, privilege_expire=0):
        """
        Build the RTC token with uid.
        :param app_id: The App ID issued to you by Agora. Apply for a new App ID from Agora Dashboard if it is missing
            from your kit. See Get an App ID.
        :param app_certificate: Certificate of the application that you registered in the Agora Dashboard.
            See Get an App Certificate.
        :param channel_name: Unique channel name for the AgoraRTC session in the string format.
        :param uid: User ID. A 32-bit unsigned integer with a value ranging from 1 to (2^32-1).
            uid must be unique.
        :param role: Role_Publisher: A broadcaster/host in a live-broadcast profile.
            Role_Subscriber: An audience(default) in a live-broadcast profile.
        :param token_expire: represented by the number of seconds elapsed since now. If, for example,
            you want to access the Agora Service within 10 minutes after the token is generated,
            set token_expire as 600(seconds).
        :param privilege_expire: represented by the number of seconds elapsed since now. If, for example,
            you want to enable your privilege for 10 minutes, set privilege_expire as 600(seconds).
        :return: The RTC token.
        """
        return RtcTokenBuilder.build_token_with_user_account(app_id, app_certificate, channel_name, uid, role, token_expire, privilege_expire)

    @staticmethod
    def build_token_with_user_account(app_id, app_certificate, channel_name, account, role, token_expire, privilege_expire=0):
        """
        Build the RTC token with account.
        :param app_id: The App ID issued to you by Agora. Apply for a new App ID from Agora Dashboard if it is missing
            from your kit. See Get an App ID.
        :param app_certificate: Certificate of the application that you registered in the Agora Dashboard.
            See Get an App Certificate.
        :param channel_name: Unique channel name for the AgoraRTC session in the string format.
        :param account: The user's account, max length is 255 Bytes.
        :param role: Role_Publisher: A broadcaster/host in a live-broadcast profile.
            Role_Subscriber: An audience(default) in a live-broadcast profile.
        :param token_expire: represented by the number of seconds elapsed since now. If, for example,
            you want to access the Agora Service within 10 minutes after the token is generated,
            set token_expire as 600(seconds).
        :param privilege_expire: represented by the number of seconds elapsed since now. If, for example,
            you want to enable your privilege for 10 minutes, set privilege_expire as 600(seconds).
        :return: The RTC token.
        """
        token = AccessToken(app_id, app_certificate, expire=token_expire)

        service_rtc = ServiceRtc(channel_name, account)
        service_rtc.add_privilege(ServiceRtc.kPrivilegeJoinChannel, privilege_expire)
        if role == Role_Publisher:
            service_rtc.add_privilege(ServiceRtc.kPrivilegePublishAudioStream, privilege_expire)
            service_rtc.add_privilege(ServiceRtc.kPrivilegePublishVideoStream, privilege_expire)
            service_rtc.add_privilege(ServiceRtc.kPrivilegePublishDataStream, privilege_expire)
        token.add_service(service_rtc)

        return token.build()
