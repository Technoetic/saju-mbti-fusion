// Source: front/js/core/saju-engine.js (callFreeAI), web/server.py (post_llm_chat).
workspace "월하몽" {
  model {
    reader = person "방문자"
    app = softwareSystem "사주경 · 월하몽"
    provider = softwareSystem "BizRouter" {
      tags "External"
    }
    reader -> app "풀이를 요청한다"
    app -> provider "생성형 풀이를 요청한다"
  }
  views {
    systemContext app "StoryContext" {
      title "생성형 풀이 요청"
      include *
      autoLayout tb
    }
    styles {
      element "Person" {
        shape Person
        background #493A48
        color #ffffff
      }
      element "Software System" {
        background #74343E
        color #ffffff
      }
      element "External" {
        background #396765
        color #ffffff
      }
    }
    terminology {
      person "사용자"
      softwareSystem "소프트웨어 시스템"
    }
  }
}
