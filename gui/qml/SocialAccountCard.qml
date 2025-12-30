import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Item {
    id: root
    property string platform: ""
    property string icon: ""
    property bool isConnected: false
    signal connect()

    Layout.fillWidth: true
    Layout.preferredHeight: 120
    
    // Hover Animation
    scale: mouseArea.containsMouse ? 1.02 : 1.0
    Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

    // Shadow
    // DropShadow {
    //     anchors.fill: bgRect
    //     source: bgRect
    //     horizontalOffset: 0
    //     verticalOffset: mouseArea.containsMouse ? 8 : 4
    //     radius: mouseArea.containsMouse ? 16 : 8
    //     samples: 17
    //     color: "#15000000"
    //     Behavior on verticalOffset { NumberAnimation { duration: 200 } }
    //     Behavior on radius { NumberAnimation { duration: 200 } }
    // }

    Rectangle {
        id: bgRect
        anchors.fill: parent
        radius: 16
        color: "white"
        border.color: mouseArea.containsMouse ? "#E0E0E0" : "#F0F0F0"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            RowLayout {
                spacing: 12
                Image {
                    source: root.icon
                    width: 32; height: 32
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                }
                Text {
                    text: root.platform
                    font.pixelSize: 16
                    font.bold: true
                    color: "#1D1D1F"
                    Layout.fillWidth: true
                }
                
                // Status Indicator
                Rectangle {
                    width: 24
                    height: 24
                    radius: 12
                    color: root.isConnected ? "#E8F5E9" : "#F5F5F5"
                    
                    Rectangle {
                        anchors.centerIn: parent
                        width: 8
                        height: 8
                        radius: 4
                        color: root.isConnected ? "#4CAF50" : "#BDBDBD"
                    }
                }
            }

            Item { Layout.fillHeight: true }

            Button {
                id: connectBtn
                text: root.isConnected ? "Connected" : "Connect"
                Layout.fillWidth: true
                Layout.preferredHeight: 36
                
                contentItem: Text {
                    text: parent.text
                    color: root.isConnected ? "#007AFF" : "white"
                    font.bold: true
                    font.pixelSize: 14
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    color: root.isConnected ? "#E1F0FF" : "#007AFF"
                    radius: 8
                    
                    gradient: root.isConnected ? null : blueGradient
                    
                    Gradient {
                        id: blueGradient
                        GradientStop { position: 0.0; color: "#007AFF" }
                        GradientStop { position: 1.0; color: "#0062CC" }
                    }
                }
                
                onClicked: root.connect()
                
                // Button internal hover
                scale: hovered ? 1.02 : 1.0
                Behavior on scale { NumberAnimation { duration: 100 } }
            }
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        onClicked: mouse.accepted = false // Let button handle clicks
    }
}
