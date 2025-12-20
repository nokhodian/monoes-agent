import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    property string platform: ""
    property string icon: ""
    property bool isConnected: false
    signal connect()

    Layout.fillWidth: true
    Layout.preferredHeight: 120
    radius: 12
    color: "white"
    border.color: "#F0F0F0"
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10

        RowLayout {
            spacing: 12
            Image {
                source: root.icon
                width: 32; height: 32
                fillMode: Image.PreserveAspectFit
            }
            Text {
                text: root.platform
                font.pixelSize: 16
                font.bold: true
                color: "#1D1D1F"
                Layout.fillWidth: true
            }
            Rectangle {
                width: 10; height: 10; radius: 5
                color: root.isConnected ? "#4CAF50" : "#D2D2D7"
            }
        }

        Item { Layout.fillHeight: true }

        Button {
            id: connectBtn
            text: root.isConnected ? "Connected" : "Connect"
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            
            background: Rectangle {
                color: root.isConnected ? "#F5F5F5" : "#007AFF"
                radius: 6
            }
            contentItem: Text {
                text: parent.text
                color: root.isConnected ? "#86868B" : "white"
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            onClicked: root.connect()
        }
    }
}
