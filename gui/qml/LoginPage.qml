import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

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
                mipmap: true
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
                    id: illustration
                    source: "../assets/Group 1667.svg"
                    anchors.centerIn: parent
                    fillMode: Image.PreserveAspectFit
                    width: parent.width * 0.8
                    mipmap: true
                    
                    // Simple entry animation
                    opacity: 1
                    // scale: 0.95
                    // Component.onCompleted: {
                    //    anim.start()
                    // }
                    // ParallelAnimation {
                    //    id: anim
                    //    NumberAnimation { target: illustration; property: "opacity"; to: 1; duration: 800; easing.type: Easing.OutQuad }
                    //    NumberAnimation { target: illustration; property: "scale"; to: 1; duration: 800; easing.type: Easing.OutBack }
                    // }
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
                    
                    // Form entry animation
                    opacity: 1
                    // transform: Translate { id: formTrans; y: 20 }
                    // Component.onCompleted: {
                    //    formAnim.start()
                    // }
                    // ParallelAnimation {
                    //    id: formAnim
                    //    NumberAnimation { target: parent; property: "opacity"; to: 1; duration: 600; easing.type: Easing.OutQuad }
                    //    NumberAnimation { target: formTrans; property: "y"; to: 0; duration: 600; easing.type: Easing.OutBack }
                    // }

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
                                border.color: tokenField.activeFocus ? "#007AFF" : "#D2D2D7"
                                border.width: tokenField.activeFocus ? 2 : 1
                                radius: 8
                                color: "white"
                                Behavior on border.color { ColorAnimation { duration: 200 } }
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
                                id: btnBg
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "#000000" }
                                    GradientStop { position: 1.0; color: "#333333" }
                                }
                                radius: 8
                                
                                layer.enabled: true
                                layer.effect: DropShadow {
                                    verticalOffset: 4
                                    radius: 8
                                    samples: 17
                                    color: "#40000000"
                                }
                            }
                            
                            scale: pressed ? 0.98 : (hovered ? 1.02 : 1.0)
                            Behavior on scale { NumberAnimation { duration: 100 } }
                            
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
                                hoverEnabled: true
                                onEntered: parent.color = "#007AFF"
                                onExited: parent.color = "#86868B"
                            }
                            Behavior on color { ColorAnimation { duration: 200 } }
                        }
                    }
                }
            }
        }
    }
}
