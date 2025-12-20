import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    property string label: ""
    property string count: "0"
    property string accentColor: "#007AFF"
    property string icon: ""

    Layout.preferredWidth: 180
    Layout.preferredHeight: 80
    radius: 12
    color: "white"
    border.color: "#F0F0F0"
    border.width: 1

    RowLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15
        
        Rectangle {
            width: 40; height: 40; radius: 20
            color: root.accentColor + "22" // 22 is ~13% alpha in hex
            
            Image {
                anchors.centerIn: parent
                source: root.icon
                width: 20; height: 20
                fillMode: Image.PreserveAspectFit
            }
        }
        
        ColumnLayout {
            spacing: 2
            Text {
                text: root.count
                font.pixelSize: 20
                font.bold: true
                color: "#1D1D1F"
            }
            Text {
                text: root.label
                font.pixelSize: 12
                color: "#86868B"
            }
        }
    }
}
