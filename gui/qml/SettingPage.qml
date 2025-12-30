import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Page {
    id: settingsPage
    objectName: "settingPage"
    background: Rectangle { color: "#F9F9F9" }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "white"
            z: 10
            
            // Header Shadow
            layer.enabled: false // true
            layer.effect: DropShadow {
                verticalOffset: 2
                radius: 8
                samples: 17
                color: "#10000000"
            }
            
            Item {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                
                Text {
                    text: "Settings"
                    font.pixelSize: 24
                    font.bold: true
                    color: "#1D1D1F"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
        
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: false // true
            
            ColumnLayout {
                width: parent.width // settingsPage.width
                spacing: 32
                
                // Content Container
                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: contentCol.implicitHeight + 64
                    
                    ColumnLayout {
                        id: contentCol
                        anchors.fill: parent
                        anchors.margins: 32
                        spacing: 32
                        
                        // General Settings Section
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "General"
                                font.pixelSize: 18
                                font.bold: true
                                color: "#1D1D1F"
                            }
                            
                            Rectangle {
                                Layout.fillWidth: true
                                height: 60
                                color: "white"
                                radius: 12
                                border.color: "#E5E5E5"
                                border.width: 1
                                
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    
                                    ColumnLayout {
                                        spacing: 4
                                        Text { 
                                            text: "Show Browser"
                                            font.pixelSize: 16
                                            font.weight: Font.Medium
                                            color: "#1D1D1F"
                                        }
                                        Text { 
                                            text: "Visualize automation actions in real-time"
                                            font.pixelSize: 13
                                            color: "#86868B"
                                        }
                                    }
                                    
                                    Item { Layout.fillWidth: true }
                                    
                                    Switch {
                                        id: headlessSwitch
                                        checked: backend.headless
                                        onToggled: backend.headless = checked
                                        
                                        indicator: Rectangle {
                                            implicitWidth: 48
                                            implicitHeight: 26
                                            x: headlessSwitch.leftPadding
                                            y: parent.height / 2 - height / 2
                                            radius: 13
                                            color: headlessSwitch.checked ? "#007AFF" : "#E5E5E5"
                                            border.color: headlessSwitch.checked ? "#007AFF" : "#E5E5E5"
                                            
                                            Rectangle {
                                                x: headlessSwitch.checked ? parent.width - width - 2 : 2
                                                y: 2
                                                width: 22
                                                height: 22
                                                radius: 11
                                                color: "white"
                                                Behavior on x { NumberAnimation { duration: 200 } }
                                            }
                                            Behavior on color { ColorAnimation { duration: 200 } }
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Social Media Accounts Section
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "Connected Accounts"
                                font.pixelSize: 18
                                font.bold: true
                                color: "#1D1D1F"
                            }
                            
                            GridLayout {
                                columns: width > 1000 ? 3 : (width > 600 ? 2 : 1)
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
                        }
                    }
                }
            }
        }
    }
}
