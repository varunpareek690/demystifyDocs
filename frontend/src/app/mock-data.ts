// A helper function to create URL-friendly IDs from titles
const slugify = (text: string): string => {
  return text.toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w-]+/g, '');
};

// The raw data you provided, with pdfFile preserved
const rawData = [
  {
    "title": "Chat 1",
    "pdfFile": "sample.pdf",
    "chat": [
      {
        "user": "What are the full names and registered addresses of the two parties involved in the service agreement?",
        "AI": "The two parties are:\nClient: The document says \"National Capital Territory of Delhi\" but doesn't give a specific name or address beyond that. It's like saying someone is from a state but not giving their street address.\nContractor: Baburao Ganpat Rao Apte, residing at Shanti Nagar, Madhuban Colony, New Delhi, Delhi, National Capital Territory of Delhi, 304023."
      },
      {
        "user": "What services will TechnoServe Solutions Private Limited provide to Bharat Industries Limited?",
        "AI": "TechnoServe will provide software development, maintenance, and consulting services to Bharat Industries. The specifics of these services are listed in a separate document called Schedule A, which is attached to the agreement."
      },
      {
        "user": "What is the payment schedule and what is the consequence of a delay in payment?",
        "AI": "The document describes a different payment arrangement between a client and a provider. Payments must be made within 30 days of receiving an invoice. If a payment is late, the client has to pay 18% yearly interest or whatever higher rate is set by the Indian Contract Act, 1872. If the client doesn't pay within 60 days, the provider can end the agreement."
      },
      {
        "user": "What happens to the intellectual property rights of the deliverables once the client makes full payment?",
        "AI": "Once the client pays everything they owe, they own the software, documents, and other things made just for them. But, there are some rules about copyrights that still apply, kind of like how a toy you buy still belongs to the toy company's idea, even though you own your toy."
      },
      {
        "user": " Under what conditions can the agreement be terminated immediately by either party?",
        "AI": "If one party seriously breaks the agreement and doesn't fix it within 30 days of getting a written warning about it, the other party can end the agreement right away. The same goes if one of the parties goes bankrupt or violates the confidentiality part of the agreement."
      }
    ]
  },
  {
    "title": "Chat 2",
    "pdfFile": "Loan Agreement.pdf",
    "chat": [
      {
        "user": "What is the total loan amount and the initial interest rate? ",
        "AI": "This document only tells us when loan payments begin (October 1, 2025) and when they end (September 1, 2028), and how they are to be paid (monthly installments). It also tells us about extra interest charged for late payments (7.9% extra per year). However, it does not say what the total loan amount is or the initial interest rate. So, I don't have enough information to answer your question."
      },
      {
        "user": "When does the interest begin to accrue on the loan? ",
        "AI": "The loan payments, which include both the original amount borrowed (principal) and interest, begin on October 1, 2025. This means the interest starts accruing then. It doesn't say if interest builds up before that date, so we don't know for sure what happens between when the loan is taken out and October 1st."
      },
      {
        "user": "What is the penalty interest rate if the principal amount is declared due and payable due to default?",
        "AI": "If the lender says you have to pay back all the money right away because you didn't follow the agreement, and you don't pay it back, then you'll have to pay extra interest. That extra interest is 7.90% each year on the amount you still owe. This extra interest starts on the day the lender tells you to pay everything back."
      },
      {
        "user": "What rights does the Lender have if the Borrower defaults on a payment?",
        "AI": "If the borrower doesn't do what they promised in the agreement, the lender can demand all the money owed right away. If the borrower still doesn't pay, the lender will charge extra interest on top of what's already owed. Also, if the borrower misses a payment or doesn't pay within 10 days of being asked, the lender can take whatever was used as security for the loan (like a car or house). It's like if you borrowed a video game from a friend and promised to return it, but didn't. Your friend could ask for it back immediately."
      },
      {
        "user": "Can the Borrower pay off the loan early without a penalty?",
        "AI": "Yes, the agreement says the borrower can make lump sum payments or pay off the entire remaining loan amount early without any extra fees or penalties, as long as they aren't currently behind on their payments."
      }
    ]
  },
];

// Process the raw data to add unique IDs and export it
export const chatHistoryData = rawData.map(item => ({
  ...item,
  id: slugify(item.title)
}));