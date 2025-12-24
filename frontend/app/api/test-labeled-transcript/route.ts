import { NextResponse } from 'next/server';

/**
 * TEMPORARY TEST ENDPOINT
 * Returns Session 5 (Family Conflict) with AI-labeled transcript
 * DELETE THIS FILE after verifying the transcript display works
 */

export async function GET() {
  // This is the actual output from our speaker labeling algorithm on Session 5
  const labeledTranscript = [
    {
      "speaker": "Therapist",
      "text": "Hi Alex. Come on in, have a seat. How are you doing today? I know last week was pretty intense.",
      "timestamp": "00:00"
    },
    {
      "speaker": "You",
      "text": "Um... not great, honestly. Something really bad happened this week. Like, I've been kind of freaking out about it. I don't even know where to start.",
      "timestamp": "00:18"
    },
    {
      "speaker": "Therapist",
      "text": "Okay, that sounds really stressful. Take your time. What happened? Just start wherever feels right.",
      "timestamp": "01:08"
    },
    {
      "speaker": "You",
      "text": "So... my mom found my insurance statements. The explanation of benefits thing. She opened my mail because she was looking for something and she saw all these charges for mental health services. And she completely flipped out.",
      "timestamp": "01:32"
    },
    {
      "speaker": "Therapist",
      "text": "Oh wow. So your family found out you're in therapy. That's a really significant breach of your privacy. How are you feeling about that?",
      "timestamp": "02:58"
    },
    {
      "speaker": "You",
      "text": "I'm just... I'm so angry and scared and guilty all at the same time. Like, I knew they wouldn't react well, but I didn't think it would be this bad. She called my dad and they both confronted me on a video call. It was like, the worst conversation of my life.",
      "timestamp": "03:23"
    },
    {
      "speaker": "Therapist",
      "text": "That sounds really overwhelming. Can you walk me through what happened in that conversation? What did they say?",
      "timestamp": "04:48"
    },
    {
      "speaker": "You",
      "text": "My mom was crying, which like, she never cries. She kept saying I was wasting money, that therapy is for weak people who can't handle their problems. My dad was just angry. He said I was being dramatic and self-indulgent. That in their generation, people just dealt with their problems instead of paying strangers to listen to them complain.",
      "timestamp": "05:13"
    },
    {
      "speaker": "Therapist",
      "text": "Those are really painful things to hear from your parents. How did you respond to them in that moment?",
      "timestamp": "07:12"
    },
    {
      "speaker": "You",
      "text": "I tried to explain that I was really struggling, that I needed help. But they just kept shutting me down. My mom said, you know, in Chinese, like, we don't air our problems to strangers. We handle things within the family. And I wanted to scream because like, I can't talk to them about this stuff. They don't get it.",
      "timestamp": "07:38"
    },
    {
      "speaker": "Therapist",
      "text": "That must have felt really invalidating. You're trying to take care of your mental health, and instead of support, you're getting criticism and shame. That's incredibly difficult.",
      "timestamp": "09:08"
    },
    {
      "speaker": "You",
      "text": "Yeah. And the worst part is my dad said if I'm going to waste their money on this, then maybe I shouldn't be in grad school at all. Like, maybe I should just come home and work instead. Which is like, his way of saying I'm a disappointment.",
      "timestamp": "09:48"
    },
    {
      "speaker": "Therapist",
      "text": "I hear you making that interpretation. When your dad said that, how did that land for you? What thoughts came up?",
      "timestamp": "11:12"
    },
    {
      "speaker": "You",
      "text": "I just felt like... like I'm this huge burden. Like I can't do anything right. They sacrificed so much to give me opportunities and I'm just throwing it all away by being mentally ill. God, I hate saying that. Mentally ill. It sounds so dramatic.",
      "timestamp": "11:48"
    },
    {
      "speaker": "Therapist",
      "text": "You're dealing with anxiety and depression, Alex. Those are real medical conditions. There's nothing dramatic about acknowledging that. Do you really believe you're throwing away their sacrifices?",
      "timestamp": "13:09"
    },
    {
      "speaker": "You",
      "text": "I don't know. Logically, no. Like, I'm still in my program. I'm still getting my PhD. But emotionally, yeah, I feel like a complete failure. Like, they came to this country with nothing and built these successful careers, and here I am, can't even function without therapy and medication.",
      "timestamp": "14:02"
    },
    {
      "speaker": "Therapist",
      "text": "I want you to notice something. You just said you feel like a failure, and then immediately gave evidence that you're not. You're pursuing a PhD in a competitive field while managing your mental health. That's actually remarkable.",
      "timestamp": "15:24"
    },
    {
      "speaker": "You",
      "text": "I guess. It doesn't feel remarkable. It feels like I'm barely holding it together. And now my parents think I'm weak and broken, which just confirms what I already thought about myself.",
      "timestamp": "16:22"
    },
    {
      "speaker": "Therapist",
      "text": "Let's pause there. I'm hearing this thought: I'm weak and broken. Where does that thought come from? Is it really your thought, or is it something you've internalized from your parents or your culture?",
      "timestamp": "17:27"
    },
    {
      "speaker": "You",
      "text": "I mean... both? I've always felt like something was wrong with me. But yeah, my parents definitely reinforced that. Like, any time I struggled with something, it was because I wasn't trying hard enough or I was being too sensitive. They never acknowledged that things could just be... hard.",
      "timestamp": "18:32"
    }
  ];

  return NextResponse.json({
    transcript: labeledTranscript,
    metadata: {
      session_id: "session_05_family_conflict",
      therapist_name: "Therapist",
      patient_label: "You",
      ai_confidence: 0.97,
      total_segments: labeledTranscript.length,
      note: "This is AI-labeled transcript from the speaker labeling algorithm. DELETE /api/test-labeled-transcript after testing."
    }
  });
}
