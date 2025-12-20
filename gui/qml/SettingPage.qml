import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Page {
    id: settingsPage
    objectName: "settingPage"
    background: Rectangle { color: "#F9F9F9" }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 30
        
        RowLayout {
            Layout.fillWidth: true
            
            Text {
                text: "Settings"
                font.pixelSize: 32
                font.bold: true
                color: "#1D1D1F"
            }
            
            Item { Layout.fillWidth: true }
            
            RowLayout {
                spacing: 10
                Text { text: "Show Browser"; color: "#86868B" }
                Switch {
                    id: headlessSwitch
                    checked: backend.headless
                    onToggled: backend.headless = checked
                }
            }
        }
        
        Text {
            text: "Social Media Accounts"
            font.pixelSize: 18
            font.bold: true
            color: "#1D1D1F"
        }
        
        GridLayout {
            columns: 3
            columnSpacing: 20
            rowSpacing: 20
            Layout.fillWidth: true
            
            SocialAccountCard {
                platform: "Instagram"
                icon: "../assets/Login-Page-Instagram.svg"
                isConnected: backend.socialStatuses["Instagram"] || false
                onConnect: backend.login_manual("INSTAGRAM")
            }
            SocialAccountCard {
                platform: "LinkedIn"
                icon: "../assets/Login-Page-Linkedin.svg"
                isConnected: backend.socialStatuses["Linkedin"] || false
                onConnect: backend.login_manual("LINKEDIN")
            }
            SocialAccountCard {
                platform: "X"
                icon: "../assets/Login-Page-X.svg"
                isConnected: backend.socialStatuses["X"] || false
                onConnect: backend.login_manual("X")
            }
            SocialAccountCard {
                platform: "TikTok"
                icon: "../assets/Login-Page-TikTok.svg"
                isConnected: backend.socialStatuses["Tiktok"] || false
                onConnect: backend.login_manual("TIKTOK")
            }
            SocialAccountCard {
                platform: "Telegram"
                icon: "../assets/Login-Page-Telegram.svg"
                isConnected: backend.socialStatuses["Telegram"] || false
                onConnect: backend.login_manual("TELEGRAM")
            }
            SocialAccountCard {
                platform: "Email"
                icon: "../assets/Login-Page-Email.png"
                isConnected: backend.socialStatuses["Email"] || false
                onConnect: backend.login_manual("EMAIL")
            }
        }
        
        Item { Layout.fillHeight: true }
    }
}
