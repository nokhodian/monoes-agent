import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Page {
    id: loginPage
    background: Rectangle { color: "white" }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            color: "transparent"
            
            Image {
                source: "../assets/monoes-logo-proper.png"
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.leftMargin: 24
                anchors.topMargin: 24
                width: 245
                fillMode: Image.PreserveAspectFit
            }
        }

        // Main Body
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Left Side (Illustration)
            Rectangle {
                Layout.fillHeight: true
                Layout.fillWidth: true
                color: "transparent"
                
                Image {
                    source: "../assets/Group 1667.svg"
                    anchors.centerIn: parent
                    fillMode: Image.PreserveAspectFit
                    width: parent.width * 0.8
                }
            }

            // Right Side (Form)
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 500
                color: "transparent"

                ColumnLayout {
                    anchors.centerIn: parent
                    width: 350
                    spacing: 30

                    ColumnLayout {
                        spacing: 10
                        Text {
                            text: "Welcome back to the community"
                            font.pixelSize: 28
                            font.family: "Inter"
                            font.bold: true
                            color: "#1D1D1F"
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Join today to collaborate with your community."
                            font.pixelSize: 16
                            font.family: "Inter"
                            color: "#86868B"
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    ColumnLayout {
                        spacing: 15
                        Layout.fillWidth: true

                        Text {
                            text: "Login"
                            font.pixelSize: 24
                            font.family: "Inter"
                            color: "#86868B"
                        }

                        TextField {
                            id: tokenField
                            placeholderText: "Enter your token..."
                            text: backend.savedToken
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            font.pixelSize: 16
                            color: "#1D1D1F"
                            background: Rectangle {
                                border.color: "#D2D2D7"
                                radius: 6
                                color: "white"
                            }
                            // Trigger login on Enter key
                            onAccepted: backend.login(text)
                        }

                        Button {
                            id: loginButton
                            text: "Login"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            
                            contentItem: Text {
                                text: parent.text
                                font.bold: true
                                font.pixelSize: 16
                                color: "white"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            background: Rectangle {
                                color: parent.pressed ? "#333333" : "black"
                                radius: 6
                            }
                            
                            onClicked: backend.login(tokenField.text)
                        }
                        
                        Text {
                            text: "Forgot Password?"
                            font.pixelSize: 14
                            color: "#86868B"
                            Layout.alignment: Qt.AlignHCenter
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }
                }
            }
        }
    }
}
